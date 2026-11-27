import pytest

from app import app, Game


@pytest.fixture
def game():
    """A fresh game with one player, Alice (p1)."""
    with app.app_context():
        g = Game("test-game")
    g.add_player("p1", "Alice")
    return g


def test_correct_answer_scores_one_point(game):
    correct = game.questions[0]["answer"]
    assert game.submit_answer("p1", 0, correct) is True
    assert game.players["p1"]["score"] == 1


def test_answering_same_question_twice_does_not_add_points(game):
    correct = game.questions[0]["answer"]
    game.submit_answer("p1", 0, correct)
    game.submit_answer("p1", 0, correct)
    assert game.players["p1"]["score"] == 1


def test_first_answer_stands_when_player_changes_their_answer(game):
    correct = game.questions[0]["answer"]
    game.submit_answer("p1", 0, "definitely wrong")
    game.submit_answer("p1", 0, correct)
    assert game.players["p1"]["score"] == 0
    assert game.players["p1"]["answers"][0] == "definitely wrong"


@pytest.mark.parametrize("player_id, question_index", [
    ("nobody", 0),     # unknown player
    ("p1", 999),       # question number too big
    ("p1", -1),        # negative question number
    ("p1", "zero"),    # not a number
    ("p1", None),      # missing
])
def test_invalid_answers_are_rejected_without_crashing(game, player_id, question_index):
    assert game.submit_answer(player_id, question_index, "anything") is False
    assert game.players["p1"]["score"] == 0


def test_colouring_square_adds_one_bonus_point(game):
    assert game.award_colouring_bonus("p1", 0) is True
    assert game.players["p1"]["score"] == 1


def test_colouring_same_question_twice_only_counts_once(game):
    game.award_colouring_bonus("p1", 0)
    assert game.award_colouring_bonus("p1", 0) is False
    assert game.players["p1"]["score"] == 1


def test_colouring_bonus_is_given_for_each_question(game):
    game.award_colouring_bonus("p1", 0)
    game.next_question("p1")  # p1 is the host, so can move everyone on
    game.award_colouring_bonus("p1", 1)
    assert game.players["p1"]["score"] == 2


def test_colouring_bonus_adds_to_correct_answer(game):
    game.submit_answer("p1", 0, game.questions[0]["answer"])
    game.award_colouring_bonus("p1", 0)
    assert game.players["p1"]["score"] == 2


@pytest.mark.parametrize("player_id, question_index", [
    ("nobody", 0),
    ("p1", 999),
    ("p1", -1),
    ("p1", "zero"),
    ("p1", None),
])
def test_invalid_colouring_bonus_is_rejected(game, player_id, question_index):
    assert game.award_colouring_bonus(player_id, question_index) is False
    assert game.players["p1"]["score"] == 0


def test_player_name_is_trimmed(game):
    game.add_player("p2", "   Bob   ")
    assert game.players["p2"]["name"] == "Bob"


def test_long_player_name_is_cut_to_20_characters(game):
    game.add_player("p2", "x" * 100)
    assert len(game.players["p2"]["name"]) == 20


@pytest.mark.parametrize("bad_name", ["", "    ", None, 12345])
def test_missing_or_odd_player_name_becomes_player(game, bad_name):
    game.add_player("p2", bad_name)
    assert game.players["p2"]["name"] == "Player"
