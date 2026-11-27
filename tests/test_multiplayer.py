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
