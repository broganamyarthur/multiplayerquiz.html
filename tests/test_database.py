import pytest

from app import app
from models import db, Question
from questions_seed import questions


def test_seed_questions_are_stored_in_database():
    with app.app_context():
        assert Question.query.count() == len(questions)


def test_stored_question_keeps_its_options_and_answer():
    with app.app_context():
        first = Question.query.order_by(Question.id).first()
        assert first.text == questions[0]["question"]
        assert first.options == questions[0]["options"]
        assert first.answer == questions[0]["answer"]


@pytest.fixture
def extra_question():
    """Add one question for a test, then remove it so other tests aren't affected."""
    with app.app_context():
        q = Question(text="Which database do the tests use?",
                     options=["SQLite", "Oracle", "Excel"], answer="SQLite")
        db.session.add(q)
        db.session.commit()
        question_id = q.id
    yield
    with app.app_context():
        db.session.delete(db.session.get(Question, question_id))
        db.session.commit()


def test_quiz_page_shows_questions_from_database(extra_question):
    response = app.test_client().get("/quiz")
    assert b"Which database do the tests use?" in response.data