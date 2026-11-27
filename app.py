from flask import Flask, render_template, request, jsonify, redirect, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import random
import os
import secrets
import time
from datetime import timedelta
from functools import wraps
from werkzeug.security import check_password_hash
from models import db, Question

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///quiz.db')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
db.init_app(app)

# Configure for production
@app.before_request
def before_request():
    if request.headers.get('X-Forwarded-Proto') == 'https':
        request.environ['wsgi.url_scheme'] = 'https'

allowed_origins = os.environ.get('ALLOWED_ORIGINS')
socketio = SocketIO(
    app,
    cors_allowed_origins=allowed_origins.split(',') if allowed_origins else None,
    async_mode='threading',
)

from questions_seed import questions
def seed_database():
    """Create the tables and add the starting questions if the table is empty."""
    db.create_all()
    if Question.query.count() == 0:
        for q in questions:
            db.session.add(Question(
                text=q["question"],
                options=q["options"],
                answer=q["answer"],
                image=q["image"],
            ))
        db.session.commit()


with app.app_context():
    seed_database()


   

def load_questions():
    """Return all questions from the database, in the format the templates expect."""
    return [
        {"question": q.text, "options": q.options, "answer": q.answer, "image": q.image}
        for q in Question.query.order_by(Question.id).all()
    ]
MAX_NAME_LENGTH = 20


def clean_player_name(name):
    """Trim a player's display name, cap its length, and fall back to "Player" if blank."""
    if not isinstance(name, str):
        return "Player"
    name = name.strip()[:MAX_NAME_LENGTH]
    return name or "Player"


games = {}
players = {}

class Game:
    def __init__(self, game_id):
        self.game_id = game_id
        self.players = {}
        self.current_question = 0
        self.started = False
        self.finished = False
        self.answers = {}
        self.questions = load_questions()
        self.colouring_bonuses = {}  # player ID -> question numbers already given a bonus
    
    def add_player(self, player_id, player_name):
        self.players[player_id] = {
            "name": clean_player_name(player_name),
            "score": 0,
            "answers": {}
        }
    
    def is_valid_question_index(self, question_index):
        """True if question_index is a whole number pointing at a real question."""
        return (
            isinstance(question_index, int)
            and not isinstance(question_index, bool)
            and 0 <= question_index < len(self.questions)
        )

    def find_player(self, player_id, question_index, action):
        """Return the player if the player and question number are valid, otherwise log and return None."""
        player = self.players.get(player_id)
        if player is None:
            app.logger.warning("Rejected %s from unknown player in game %s", action, self.game_id)
            return None
        if not self.is_valid_question_index(question_index):
            app.logger.warning("Rejected %s with invalid question index %r in game %s",
                               action, question_index, self.game_id)
            return None
        return player

    def submit_answer(self, player_id, question_index, answer):
        """Record a player's first answer to a question. Returns False if rejected."""
        player = self.find_player(player_id, question_index, "answer")
        if player is None:
            return False
        if question_index in player["answers"]:
            return False  # first answer stands
        player["answers"][question_index] = answer
        if answer == self.questions[question_index]["answer"]:
            player["score"] += 1
        return True

    def award_colouring_bonus(self, player_id, question_index):
        """Give 1 bonus point the first time a player colours in the square for a question."""
        player = self.find_player(player_id, question_index, "colouring bonus")
        if player is None:
            return False
        already_given = self.colouring_bonuses.setdefault(player_id, set())
        if question_index in already_given:
            return False  # only one bonus per question
        already_given.add(question_index)
        player["score"] += 1
        return True

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/admin")
def admin_page():
    """Question bank admin page. Questions load from the API after sign-in."""
    return render_template("admin.html")    

@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})

MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 15 * 60
failed_logins = {}  # IP address -> times of recent failed sign-ins


def is_locked_out(ip):
    """True if this IP has 5 or more failed sign-ins in the last 15 minutes."""
    recent = [t for t in failed_logins.get(ip, []) if time.time() - t < LOCKOUT_SECONDS]
    failed_logins[ip] = recent
    return len(recent) >= MAX_FAILED_LOGINS


@app.route("/api/login", methods=["POST"])
def login():
    """Sign in as admin if the password matches the stored hash."""
    ip = request.remote_addr
    if is_locked_out(ip):
        return jsonify({"error": "Too many failed attempts. Try again later."}), 429
    data = request.get_json(silent=True) or {}
    password = str(data.get("password", ""))
    password_hash = os.environ.get("ADMIN_PASSWORD_HASH")
    if not password_hash or not check_password_hash(password_hash, password):
        failed_logins.setdefault(ip, []).append(time.time())
        return jsonify({"error": "Incorrect password"}), 401
    failed_logins.pop(ip, None)
    session.clear()
    session["is_admin"] = True
    session.permanent = True
    return jsonify({"status": "signed in"})


@app.route("/api/logout", methods=["POST"])
def logout():
    """Sign out by clearing the session."""
    session.clear()
    return jsonify({"status": "signed out"})

def admin_required(view):
    """Refuse the request with 401 unless the user is signed in as admin."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return jsonify({"error": "Admin sign-in required"}), 401
        return view(*args, **kwargs)
    return wrapper

@app.route("/api/questions", methods=["GET"])
@admin_required
def list_questions():
    """Return questions, optionally filtered by ?search= keyword and ?category=."""
    query = Question.query
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    if search:
        query = query.filter(Question.text.ilike(f"%{search}%"))
    if category:
        query = query.filter(Question.category == category)
    return jsonify([q.to_dict() for q in query.order_by(Question.id).all()])

@app.route("/api/questions/<int:question_id>", methods=["GET"])
@admin_required
def get_question(question_id):
    """Return one question, or 404 if it doesn't exist."""
    question = db.get_or_404(Question, question_id)
    return jsonify(question.to_dict())

def validate_question(data):
    """Return an error message if the question data is invalid, otherwise None."""
    if not isinstance(data, dict):
        return "Request body must be JSON"
    text = (data.get("text") or "").strip()
    options = data.get("options")
    answer = data.get("answer")
    if not text:
        return "Question text is required"
    if not isinstance(options, list) or len(options) < 2:
        return "At least 2 options are required"
    if answer not in options:
        return "The answer must be one of the options"
    return None


@app.route("/api/questions", methods=["POST"])
@admin_required
def create_question():
    """Add a new question to the question bank."""
    data = request.get_json(silent=True)
    error = validate_question(data)
    if error:
        return jsonify({"error": error}), 400
    question = Question(
        text=data["text"].strip(),
        options=data["options"],
        answer=data["answer"],
        image=data.get("image"),
        category=data.get("category"),
    )
    db.session.add(question)
    db.session.commit()
    return jsonify(question.to_dict()), 201

@app.route("/api/questions/<int:question_id>", methods=["PUT"])
@admin_required
def update_question(question_id):
    """Replace a question's details, after checking they are valid."""
    question = db.get_or_404(Question, question_id)
    data = request.get_json(silent=True)
    error = validate_question(data)
    if error:
        return jsonify({"error": error}), 400
    question.text = data["text"].strip()
    question.options = data["options"]
    question.answer = data["answer"]
    question.image = data.get("image")
    question.category = data.get("category")
    db.session.commit()
    return jsonify(question.to_dict())

@app.route("/api/questions/<int:question_id>", methods=["DELETE"])
@admin_required
def delete_question(question_id):
    """Remove a question from the question bank."""
    question = db.get_or_404(Question, question_id)
    db.session.delete(question)
    db.session.commit()
    return "", 204

@app.route("/quiz")
def quiz():
    return render_template("quiz.html", questions=load_questions())

@app.route("/submit", methods=["POST"])
def submit():
    questions = load_questions()
    score = 0
    for i, q in enumerate(questions):
        user_answer = request.form.get(f"q{i}")
        if user_answer == q["answer"]:
            score += 1

    host_reactions = [
        "Fantastic performance!",
        "Not bad at all!",
        "You can do better — try again!",
        "Impressive knowledge!",
        "A solid effort!"
    ]

    return render_template(
        "result.html",
        score=score,
        total=len(questions),
        host_message=random.choice(host_reactions)    # nosec B311 # picks a cosmetic host message, not used for security
    )

@app.route("/multiplayer")
def multiplayer():
    player_name = request.args.get("name", "Player")
    # Create a new game
    game_id = str(uuid.uuid4())[:8]
    player_id = str(uuid.uuid4())
    
    game = Game(game_id)
    game.add_player(player_id, player_name)
    games[game_id] = game
    players[player_id] = {"game_id": game_id, "name": player_name}
    
    return redirect(f"/lobby/{game_id}")

@app.route("/lobby/<game_id>")
def lobby(game_id):
    return render_template("lobby.html", game_id=game_id)

@app.route("/multiplayer_quiz/<game_id>")
def multiplayer_quiz(game_id):
    game = games.get(game_id)
    if not game:
        return redirect("/")
    return render_template("multiplayer_quiz.html", game_id=game_id, questions=game.questions)

@app.route("/multiplayer_result/<game_id>")
def multiplayer_result(game_id):
    game = games.get(game_id)
    if not game:
        return redirect("/")
    
    # Convert game object to dictionary for JSON serialization
    game_dict = {
        "game_id": game.game_id,
        "players": game.players,
        "started": game.started,
        "finished": game.finished
    }
    return render_template("multiplayer_result.html", game=game_dict, game_id=game_id, questions=game.questions)

@socketio.on("create_game")
def on_create_game(data):
    game_id = str(uuid.uuid4())[:8]
    player_name = data.get("player_name", "Player")
    player_id = str(uuid.uuid4())
    
    game = Game(game_id)
    game.add_player(player_id, player_name)
    games[game_id] = game
    players[player_id] = {"game_id": game_id, "name": player_name}
    
    join_room(game_id)
    emit("game_created", {"game_id": game_id, "player_id": player_id, "player_name": player_name})

@socketio.on("join_game")
def on_join_game(data):
    game_id = data.get("game_id")
    player_name = data.get("player_name", "Player")
    player_id = str(uuid.uuid4())
    
    if game_id not in games:
        emit("error", {"message": "Game not found"})
        return
    
    game = games[game_id]
    if game.started:
        emit("error", {"message": "Game already started"})
        return
    
    game.add_player(player_id, player_name)
    players[player_id] = {"game_id": game_id, "name": player_name}
    
    join_room(game_id)
    # Tell only the joining player their own ID...
    emit("joined_game", {"game_id": game_id, "player_id": player_id,
                         "player_name": game.players[player_id]["name"]})
    # ...and tell everyone in the room the updated player list, without that ID,
    # so other players' pages can't mistake it for their own.
    emit("player_joined", {"player_name": game.players[player_id]["name"],
                           "players": game.players}, to=game_id)

@socketio.on("get_game_state")
def on_get_game_state(data):
    game_id = data.get("game_id")
    
    if game_id not in games:
        emit("error", {"message": "Game not found"})
        return
    
    game = games[game_id]
    emit("game_state", {"players": game.players})

@socketio.on("join_room")
def on_join_room(data):
    game_id = data.get("game_id")
    join_room(game_id)

@socketio.on("start_game")
def on_start_game(data):
    game_id = data.get("game_id")
    
    if game_id not in games:
        emit("error", {"message": "Game not found"})
        return
    
    game = games[game_id]
    game.started = True
    
    emit("game_started", {"total_questions": len(game.questions)}, to=game_id)

@socketio.on("submit_answer")
def on_submit_answer(data):
    game_id = data.get("game_id")
    player_id = data.get("player_id")
    question_index = data.get("question_index")
    answer = data.get("answer")
    
    if game_id not in games:
        emit("error", {"message": "Game not found"})
        return
    
    game = games[game_id]
    if not game.submit_answer(player_id, question_index, answer):
        emit("error", {"message": "Answer not accepted"})
        return
    
    # Broadcast updated leaderboard to all players in game
    emit("leaderboard_update", {"players": game.players}, to=game_id)


@socketio.on("colouring_complete")
def on_colouring_complete(data):
    """A player finished colouring in the square: give a bonus point once per question."""
    game = games.get(data.get("game_id"))
    if game is None:
        emit("error", {"message": "Game not found"})
        return
    if game.award_colouring_bonus(data.get("player_id"), data.get("question_index")):
        emit("leaderboard_update", {"players": game.players}, to=game.game_id)

@socketio.on("finish_game")
def on_finish_game(data):
    game_id = data.get("game_id")
    
    print(f"Finish game request for: {game_id}")
    print(f"Available games: {list(games.keys())}")
    
    if game_id not in games:
        emit("error", {"message": "Game not found"})
        return
    
    game = games[game_id]
    game.finished = True
    
    # Sort players by score
    sorted_players = sorted(game.players.items(), key=lambda x: x[1]["score"], reverse=True)
    
    print(f"Emitting game_finished to room {game_id}")
    emit("game_finished", {"results": sorted_players}, to=game_id)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=port, debug=False)
