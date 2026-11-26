from app import app
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