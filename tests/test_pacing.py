"""Unit tests for US-03 host-controlled pacing and US-07 late answers."""
import pytest

from app import app, Game


@pytest.fixture
def game():
    """A game where Alice (host) created it and Bob (guest) joined."""
    with app.app_context():
        g = Game("pace-game")
    g.add_player("host", "Alice")
    g.add_player("guest", "Bob")
    return g


def test_first_player_to_join_is_the_host(game):
    assert game.host_id == "host"


def test_game_starts_on_the_first_question(game):
    assert game.current_question == 0


def test_host_can_move_everyone_to_the_next_question(game):
    assert game.next_question("host") is True
    assert game.current_question == 1


def test_other_players_cannot_move_to_the_next_question(game):
    assert game.next_question("guest") is False
    assert game.current_question == 0


def test_cannot_move_past_the_last_question(game):
    last = len(game.questions) - 1
    game.current_question = last
    assert game.next_question("host") is False
    assert game.current_question == last


def test_late_answer_to_a_closed_question_is_not_scored(game):
    correct = game.questions[0]["answer"]
    game.next_question("host")
    assert game.submit_answer("guest", 0, correct) is False
    assert game.players["guest"]["score"] == 0


def test_answer_to_a_question_not_shown_yet_is_rejected(game):
    assert game.submit_answer("guest", 1, game.questions[1]["answer"]) is False


def test_late_colouring_bonus_is_not_given(game):
    game.next_question("host")
    assert game.award_colouring_bonus("guest", 0) is False


def test_host_can_see_how_many_players_have_answered(game):
    assert game.answer_count() == 0
    game.submit_answer("guest", 0, "anything")
    assert game.answer_count() == 1
    game.submit_answer("host", 0, "anything")
    assert game.answer_count() == 2
