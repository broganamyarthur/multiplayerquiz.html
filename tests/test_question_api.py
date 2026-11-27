import pytest

from app import app
from conftest import TEST_ADMIN_PASSWORD
from models import db, Question
from questions_seed import questions


@pytest.fixture
def admin():
    """A test client that is signed in as admin."""
    client = app.test_client()
    client.post("/api/login", json={"password": TEST_ADMIN_PASSWORD})
    return client


def make_question():
    """Add a temporary question for a test and return its ID."""
    with app.app_context():
        q = Question(text="Temporary question", options=["A", "B"], answer="A")
        db.session.add(q)
        db.session.commit()
        return q.id


def delete_question_if_present(question_id):
    """Remove a temporary question so other tests aren't affected."""
    with app.app_context():
        q = db.session.get(Question, question_id)
        if q:
            db.session.delete(q)
            db.session.commit()


def test_question_api_refuses_anonymous_users():
    client = app.test_client()
    assert client.get("/api/questions").status_code == 401
    assert client.post("/api/questions", json={}).status_code == 401
    assert client.put("/api/questions/99999", json={}).status_code == 401
    assert client.delete("/api/questions/99999").status_code == 401


def test_signing_out_removes_admin_access(admin):
    admin.post("/api/logout")
    assert admin.get("/api/questions").status_code == 401


def test_list_questions_returns_all_questions(admin):
    response = admin.get("/api/questions")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == len(questions)
    assert data[0]["text"] == questions[0]["question"]


def test_get_one_question_by_id(admin):
    response = admin.get("/api/questions/1")
    assert response.status_code == 200
    assert response.get_json()["text"] == questions[0]["question"]


def test_get_missing_question_returns_404(admin):
    response = admin.get("/api/questions/99999")
    assert response.status_code == 404


def test_create_question_saves_it(admin):
    new = {
        "text": "What does CI stand for?",
        "options": ["Continuous Integration", "Code Inspection"],
        "answer": "Continuous Integration",
        "category": "DevOps",
    }
    response = admin.post("/api/questions", json=new)
    assert response.status_code == 201
    created = response.get_json()
    assert created["text"] == new["text"]
    delete_question_if_present(created["id"])


def test_create_question_rejects_answer_not_in_options(admin):
    bad = {"text": "Pick one", "options": ["A", "B"], "answer": "C"}
    assert admin.post("/api/questions", json=bad).status_code == 400


def test_create_question_rejects_fewer_than_two_options(admin):
    bad = {"text": "Pick one", "options": ["A"], "answer": "A"}
    assert admin.post("/api/questions", json=bad).status_code == 400


def test_create_question_rejects_missing_text(admin):
    bad = {"text": "", "options": ["A", "B"], "answer": "A"}
    assert admin.post("/api/questions", json=bad).status_code == 400


def test_update_question_saves_changes(admin):
    question_id = make_question()
    changed = {"text": "Updated question", "options": ["A", "B", "C"], "answer": "C"}
    response = admin.put(f"/api/questions/{question_id}", json=changed)
    assert response.status_code == 200
    assert response.get_json()["text"] == "Updated question"
    delete_question_if_present(question_id)


def test_update_question_rejects_invalid_data(admin):
    question_id = make_question()
    bad = {"text": "Updated", "options": ["A", "B"], "answer": "Z"}
    assert admin.put(f"/api/questions/{question_id}", json=bad).status_code == 400
    delete_question_if_present(question_id)


def test_update_missing_question_returns_404(admin):
    changed = {"text": "Updated", "options": ["A", "B"], "answer": "A"}
    assert admin.put("/api/questions/99999", json=changed).status_code == 404


def test_delete_question_removes_it(admin):
    question_id = make_question()
    assert admin.delete(f"/api/questions/{question_id}").status_code == 204
    with app.app_context():
        assert db.session.get(Question, question_id) is None


def test_delete_missing_question_returns_404(admin):
    assert admin.delete("/api/questions/99999").status_code == 404


def test_search_questions_by_keyword(admin):
    response = admin.get("/api/questions?search=planet")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 1
    assert all("planet" in q["text"].lower() for q in data)


def test_search_questions_by_category(admin):
    with app.app_context():
        q = Question(text="Which tool runs our pipeline?",
                     options=["GitHub Actions", "Excel"],
                     answer="GitHub Actions", category="DevOps")
        db.session.add(q)
        db.session.commit()
        question_id = q.id
    data = admin.get("/api/questions?category=DevOps").get_json()
    assert [q["id"] for q in data] == [question_id]
    delete_question_if_present(question_id)