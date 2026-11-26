from app import app
from models import Question
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