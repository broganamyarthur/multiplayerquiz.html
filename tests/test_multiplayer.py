"""Integration tests for multiplayer, using Flask-SocketIO's test client.

Each test_client acts like a separate browser tab connected to the server.
"""
from app import app, socketio, games


def last_event(client, name):
    """Return the data of the last event called `name` this client received, or None."""
    events = [e for e in client.get_received() if e["name"] == name]
    return events[-1]["args"][0] if events else None


def host_and_guest():
    """Alice creates a game, then Bob joins it from a second connection."""
    host = socketio.test_client(app)
    host.emit("create_game", {"player_name": "Alice"})
    created = last_event(host, "game_created")
    guest = socketio.test_client(app)
    guest.emit("join_game", {"game_id": created["game_id"], "player_name": "Bob"})
    return host, guest, created


def test_joining_player_is_told_their_own_id():
    host, guest, created = host_and_guest()
    joined = last_event(guest, "joined_game")
    assert joined is not None
    game = games[created["game_id"]]
    assert game.players[joined["player_id"]]["name"] == "Bob"


def test_other_players_are_not_sent_the_new_players_id():
    host, guest, created = host_and_guest()
    update = last_event(host, "player_joined")
    assert update is not None
    assert "player_id" not in update
    assert len(update["players"]) == 2


def test_host_moving_on_shows_the_next_question_to_everyone():
    host, guest, created = host_and_guest()
    guest.get_received()  # ignore earlier messages
    host.emit("next_question", {"game_id": created["game_id"], "player_id": created["player_id"]})
    assert last_event(guest, "show_question") == {"question_index": 1}


def test_guest_cannot_move_everyone_on():
    host, guest, created = host_and_guest()
    guest_id = last_event(guest, "joined_game")["player_id"]
    host.get_received()
    guest.emit("next_question", {"game_id": created["game_id"], "player_id": guest_id})
    assert last_event(host, "show_question") is None


def test_guest_cannot_finish_the_game():
    host, guest, created = host_and_guest()
    guest_id = last_event(guest, "joined_game")["player_id"]
    host.get_received()
    guest.emit("finish_game", {"game_id": created["game_id"], "player_id": guest_id})
    assert last_event(host, "game_finished") is None


def test_host_is_told_how_many_players_have_answered():
    host, guest, created = host_and_guest()
    guest_id = last_event(guest, "joined_game")["player_id"]
    host.get_received()
    guest.emit("submit_answer", {"game_id": created["game_id"], "player_id": guest_id,
                                 "question_index": 0, "answer": "anything"})
    assert last_event(host, "answer_count") == {"question_index": 0, "answered": 1, "players": 2}


# --- US-01 and US-02: hosting and joining (these check behaviour that already works) ---

def test_host_is_given_a_join_code():
    host = socketio.test_client(app)
    host.emit("create_game", {"player_name": "Alice"})
    created = last_event(host, "game_created")
    assert len(created["game_id"]) == 8
    assert created["game_id"] in games


def test_joining_with_a_wrong_code_gives_an_error():
    client = socketio.test_client(app)
    client.emit("join_game", {"game_id": "nope", "player_name": "Bob"})
    assert last_event(client, "error") == {"message": "Game not found"}


def test_nobody_can_join_after_the_game_starts():
    host, guest, created = host_and_guest()
    host.emit("start_game", {"game_id": created["game_id"], "player_id": created["player_id"]})
    late = socketio.test_client(app)
    late.emit("join_game", {"game_id": created["game_id"], "player_name": "Cara"})
    assert last_event(late, "error") == {"message": "Game already started"}


# --- US-04: leaderboard ---

def test_everyone_gets_the_updated_leaderboard_after_an_answer():
    host, guest, created = host_and_guest()
    guest_id = last_event(guest, "joined_game")["player_id"]
    correct = games[created["game_id"]].questions[0]["answer"]
    host.get_received()
    guest.emit("submit_answer", {"game_id": created["game_id"], "player_id": guest_id,
                                 "question_index": 0, "answer": correct})
    update = last_event(host, "leaderboard_update")
    assert update["players"][guest_id]["score"] == 1
