from flask import Flask, render_template, request, jsonify, redirect
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import random
import os
import secrets
from models import db, Question

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///quiz.db')
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
    
    def add_player(self, player_id, player_name):
        self.players[player_id] = {
            "name": player_name,
            "score": 0,
            "answers": {}
        }
    
    def submit_answer(self, player_id, question_index, answer):
        if answer == self.questions[question_index]["answer"]:
            self.players[player_id]["score"] += 1
        self.players[player_id]["answers"][question_index] = answer

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})

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
    emit("player_joined", {"player_id": player_id, "player_name": player_name, "players": game.players}, to=game_id)

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
    game.submit_answer(player_id, question_index, answer)
    
    # Broadcast updated leaderboard to all players in game
    emit("leaderboard_update", {"players": game.players}, to=game_id)

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
