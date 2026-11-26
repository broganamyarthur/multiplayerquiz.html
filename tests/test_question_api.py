from app import app
from models import db, Question
from questions_seed import questions


def test_list_questions_returns_all_questions():
    response = app.test_client().get("/api/questions")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == len(questions)
    assert data[0]["text"] == questions[0]["question"]


def test_get_one_question_by_id():
    response = app.test_client().get("/api/questions/1")
    assert response.status_code == 200
    assert response.get_json()["text"] == questions[0]["question"]


def test_get_missing_question_returns_404():
    response = app.test_client().get("/api/questions/99999")
    assert response.status_code == 404


def test_create_question_saves_it():
    new = {
        "text": "What does CI stand for?",
        "options": ["Continuous Integration", "Code Inspection"],
        "answer": "Continuous Integration",
        "category": "DevOps",
    }
    response = app.test_client().post("/api/questions", json=new)
    assert response.status_code == 201
    created = response.get_json()
    assert created["text"] == new["text"]
    with app.app_context():
        saved = db.session.get(Question, created["id"])
        assert saved is not None
        db.session.delete(saved)
        db.session.commit()


def test_create_question_rejects_answer_not_in_options():
    bad = {"text": "Pick one", "options": ["A", "B"], "answer": "C"}
    response = app.test_client().post("/api/questions", json=bad)
    assert response.status_code == 400


def test_create_question_rejects_fewer_than_two_options():
    bad = {"text": "Pick one", "options": ["A"], "answer": "A"}
    response = app.test_client().post("/api/questions", json=bad)
    assert response.status_code == 400


def test_create_question_rejects_missing_text():
    bad = {"text": "", "options": ["A", "B"], "answer": "A"}
    response = app.test_client().post("/api/questions", json=bad)
    assert response.status_code == 400