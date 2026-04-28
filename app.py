from flask import Flask, render_template, request, jsonify, redirect
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import random
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# Configure for production
@app.before_request
def before_request():
    if request.headers.get('X-Forwarded-Proto') == 'https':
        request.environ['wsgi.url_scheme'] = 'https'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

questions = [
    {
        "question": "What year did the Berlin Wall fall?",
        "options": ["1987", "1989", "1991"],
        "answer": "1989",
        "image": "https://images.unsplash.com/photo-1524661135-423995f22d0b?w=400&h=300&fit=crop"
    },
    {
        "question": "Which planet is known as the Red Planet?",
        "options": ["Mars", "Jupiter", "Venus"],
        "answer": "Mars",
        "image": "https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=400&h=300&fit=crop"
    },
    {
        "question": "Who wrote 'The Old Man and the Sea'?",
        "options": ["Ernest Hemingway", "Mark Twain", "George Orwell"],
        "answer": "Ernest Hemingway",
        "image": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&h=300&fit=crop"
    },
    {
        "question": "What is the largest ocean on Earth?",
        "options": ["Atlantic Ocean", "Indian Ocean", "Pacific Ocean"],
        "answer": "Pacific Ocean",
        "image": "https://images.unsplash.com/photo-1505142468610-359e7d316be0?w=400&h=300&fit=crop"
    },
    {
        "question": "Which country invented the sport of golf?",
        "options": ["Ireland", "Scotland", "England"],
        "answer": "Scotland",
        "image": "https://upload.wikimedia.org/wikipedia/commons/6/6e/Golfer_swing.jpg"
    },
    {
        "question": "Who played John McClane in 'Die Hard'?",
        "options": ["Bruce Willis", "Mel Gibson", "Tom Cruise"],
        "answer": "Bruce Willis",
        "image": "https://upload.wikimedia.org/wikipedia/commons/c/c4/Bruce_Willis_by_Gage_Skidmore_3.jpg"
    },
    {
        "question": "What year was the first Matrix movie released?",
        "options": ["1997", "1999", "2001"],
        "answer": "1999",
        "image": "https://upload.wikimedia.org/wikipedia/commons/2/26/Keanu_Reeves_and_Carrie_Ann_Moss_shoot_motorcycle_scene_for_Matrix_4_%28cropped%29.jpg"
    },
    {
        "question": "Which TV series features Tony Soprano?",
        "options": ["Breaking Bad", "The Sopranos", "Boardwalk Empire"],
        "answer": "The Sopranos",
        "image": "https://upload.wikimedia.org/wikipedia/commons/1/1f/James_Gandolfini_%40_Toronto_International_Film_Festival_2011.jpg"
    },
    {
        "question": "Who directed Jurassic Park?",
        "options": ["James Cameron", "Steven Spielberg", "Ridley Scott"],
        "answer": "Steven Spielberg",
        "image": "https://upload.wikimedia.org/wikipedia/commons/c/ca/MKr25380_Steven_Spielberg_%28Berlinale_2023%29.jpg"
    },
    {
        "question": "What is the name of Rocky Balboa's trainer?",
        "options": ["Mickey", "Apollo", "Duke"],
        "answer": "Mickey",
        "image": "https://upload.wikimedia.org/wikipedia/commons/a/a2/Sylvester_Stallone_-_1977.jpg"
    },
    {
        "question": "Which band released 'Dark Side of the Moon'?",
        "options": ["Pink Floyd", "The Beatles", "Led Zeppelin"],
        "answer": "Pink Floyd",
        "image": "https://upload.wikimedia.org/wikipedia/commons/4/4c/Pink_Floyd_at_Live_8%2C_London.jpg"
    },
    {
        "question": "Who was the lead singer of Nirvana?",
        "options": ["Kurt Cobain", "Eddie Vedder", "Chris Cornell"],
        "answer": "Kurt Cobain",
        "image": "https://upload.wikimedia.org/wikipedia/commons/1/1e/Photo_of_Kurt_Cobain_from_US_Embassy_in_Bern.jpg"
    },
    {
        "question": "What year did Michael Jackson release 'Thriller'?",
        "options": ["1980", "1982", "1984"],
        "answer": "1982",
        "image": "https://upload.wikimedia.org/wikipedia/commons/b/b9/Michael_Jackson_1983_%283x4_cropped%29_%28contrast%29.jpg"
    },
    {
        "question": "Which rock band is known for 'Hotel California'?",
        "options": ["Eagles", "Fleetwood Mac", "The Rolling Stones"],
        "answer": "Eagles",
        "image": "https://upload.wikimedia.org/wikipedia/commons/1/11/The_Eagles_in_performance%2C_2008.jpg"
    },
    {
        "question": "Who is the guitarist famous for 'Purple Haze'?",
        "options": ["Eric Clapton", "Jimi Hendrix", "Jimmy Page"],
        "answer": "Jimi Hendrix",
        "image": "https://upload.wikimedia.org/wikipedia/commons/a/aa/Jimi_Hendrix_%281967%29_%28cropped%29.jpg"
    },
    {
        "question": "Which country won the 1998 FIFA World Cup?",
        "options": ["Brazil", "France", "Germany"],
        "answer": "France",
        "image": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=400&h=300&fit=crop"
    },
    {
        "question": "Who holds the record for the most Formula 1 championships?",
        "options": ["George Russell", "Lewis Hamilton", "Ayrton Senna"],
        "answer": "Lewis Hamilton",
        "image": "https://upload.wikimedia.org/wikipedia/commons/f/f0/2024-08-24_Motorsport%2C_Formel_1%2C_Gro%C3%9Fer_Preis_der_Niederlande_2024_STP_3314_by_Stepro.jpg"
    },
    {
        "question": "In boxing, how many minutes is a standard round?",
        "options": ["2 minutes", "3 minutes", "5 minutes"],
        "answer": "3 minutes",
        "image": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=400&h=300&fit=crop"
    },
    {
        "question": "What sport uses the term 'birdie'?",
        "options": ["Tennis", "Golf", "Badminton"],
        "answer": "Golf",
        "image": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=400&h=300&fit=crop"
    },
    {
        "question": "Who is known as 'The Great One' in ice hockey?",
        "options": ["Wayne Gretzky", "Mario Lemieux", "Bobby Orr"],
        "answer": "Wayne Gretzky",
        "image": "https://upload.wikimedia.org/wikipedia/commons/c/cc/Andrew_Scheer_with_Wayne_Gretzky_%2848055697168%29_%28cropped%29.jpg"
    },
    {
        "question": "What car company manufactures the Mustang?",
        "options": ["Ford", "Chevrolet", "Dodge"],
        "answer": "Ford",
        "image": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=300&fit=crop"
    },
    {
        "question": "What does ABS stand for?",
        "options": ["Automatic Braking System", "Anti-lock Braking System", "Advanced Balance System"],
        "answer": "Anti-lock Braking System",
        "image": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=400&h=300&fit=crop"
    },
    {
        "question": "Which company created the first iPhone?",
        "options": ["Samsung", "Apple", "Nokia"],
        "answer": "Apple",
        "image": "https://images.unsplash.com/photo-1523206489230-c012066d937a?w=400&h=300&fit=crop"
    },
    {
        "question": "What does CPU stand for?",
        "options": ["Central Processing Unit", "Computer Power Unit", "Core Performance Utility"],
        "answer": "Central Processing Unit",
        "image": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=400&h=300&fit=crop"
    },
    {
        "question": "Which car brand has a bull as its logo?",
        "options": ["Ferrari", "Lamborghini", "Maserati"],
        "answer": "Lamborghini",
        "image": "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=400&h=300&fit=crop"
    },
    {
        "question": "What tool is used to measure electrical current?",
        "options": ["Voltmeter", "Ammeter", "Ohmmeter"],
        "answer": "Ammeter",
        "image": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=400&h=300&fit=crop"
    },
    {
        "question": "What does PSI measure?",
        "options": ["Temperature", "Pressure", "Speed"],
        "answer": "Pressure",
        "image": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400&h=300&fit=crop"
    },
    {
        "question": "How many hearts does an octopus have?",
        "options": ["1", "2", "3"],
        "answer": "3",
        "image": "https://images.unsplash.com/photo-1527489377706-5bf97e608852?w=400&h=300&fit=crop"
    },
    {
        "question": "What is WD-40 primarily used for?",
        "options": ["Cleaning glass", "Lubrication and rust prevention", "Polishing wood"],
        "answer": "Lubrication and rust prevention",
        "image": "https://images.unsplash.com/photo-1453614512568-c4024d13c247?w=400&h=300&fit=crop"
    },
    {
        "question": "Which country drinks the most tea?",
        "options": ["China", "India", "Turkey"],
        "answer": "Turkey",
        "image": "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=400&h=300&fit=crop"
    },
    {
        "question": "What grain is used to make traditional Scotch whisky?",
        "options": ["Wheat", "Barley", "Rye"],
        "answer": "Barley",
        "image": "https://images.unsplash.com/photo-1608270861620-7191c49a1b27?w=400&h=300&fit=crop"
    },
    {
        "question": "Which country is famous for Kobe beef?",
        "options": ["Japan", "USA", "Australia"],
        "answer": "Japan",
        "image": "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=400&h=300&fit=crop"
    },
    {
        "question": "What is the main ingredient in guacamole?",
        "options": ["Avocado", "Cucumber", "Zucchini"],
        "answer": "Avocado",
        "image": "https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?w=400&h=300&fit=crop"
    },
    {
        "question": "What type of beer is Guinness?",
        "options": ["Lager", "Stout", "Pilsner"],
        "answer": "Stout",
        "image": "https://images.unsplash.com/photo-1535958636474-b021ee887b13?w=400&h=300&fit=crop"
    },
    {
        "question": "What spice is known as 'the king of spices'?",
        "options": ["Cinnamon", "Black pepper", "Nutmeg"],
        "answer": "Black pepper",
        "image": "https://images.unsplash.com/photo-1596040143159-a5f64e0b5238?w=400&h=300&fit=crop"
    }
]

# Store active games
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
    
    def add_player(self, player_id, player_name):
        self.players[player_id] = {
            "name": player_name,
            "score": 0,
            "answers": {}
        }
    
    def submit_answer(self, player_id, question_index, answer):
        if answer == questions[question_index]["answer"]:
            self.players[player_id]["score"] += 1
        self.players[player_id]["answers"][question_index] = answer

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/quiz")
def quiz():
    return render_template("quiz.html", questions=questions)

@app.route("/submit", methods=["POST"])
def submit():
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
        host_message=random.choice(host_reactions)
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
    return render_template("multiplayer_quiz.html", game_id=game_id, questions=questions)

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
    return render_template("multiplayer_result.html", game=game_dict, game_id=game_id, questions=questions)

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
    
    emit("game_started", {"total_questions": len(questions)}, to=game_id)

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
    socketio.run(app, host="0.0.0.0", port=port)
