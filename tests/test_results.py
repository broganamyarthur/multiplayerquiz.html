"""Unit tests for US-04: ranking players on the results page."""
from app import rank_players


def test_players_are_ranked_highest_score_first():
    ranked = rank_players({
        "a": {"name": "Alice", "score": 3},
        "b": {"name": "Bob", "score": 5},
    })
    assert [(p["name"], p["rank"]) for p in ranked] == [("Bob", 1), ("Alice", 2)]


def test_players_with_the_same_score_share_a_rank():
    ranked = rank_players({
        "a": {"name": "Alice", "score": 5},
        "b": {"name": "Bob", "score": 5},
        "c": {"name": "Cara", "score": 2},
    })
    assert [p["rank"] for p in ranked] == [1, 1, 3]


def test_ranking_does_not_reveal_player_ids():
    ranked = rank_players({"secret-id": {"name": "Alice", "score": 1, "answers": {}}})
    assert ranked == [{"name": "Alice", "score": 1, "rank": 1}]
