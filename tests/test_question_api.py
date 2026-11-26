from app import app
from questions_seed import questions


def test_list_questions_returns_all_questions():
    response = app.test_client().get("/api/questions")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == len(questions)
    assert data[0]["text"] == questions[0]["question"]