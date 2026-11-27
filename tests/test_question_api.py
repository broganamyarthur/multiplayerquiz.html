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


def test_update_question_saves_changes():
    question_id = make_question()
    changed = {"text": "Updated question", "options": ["A", "B", "C"], "answer": "C"}
    response = app.test_client().put(f"/api/questions/{question_id}", json=changed)
    assert response.status_code == 200
    assert response.get_json()["text"] == "Updated question"
    delete_question_if_present(question_id)


def test_update_question_rejects_invalid_data():
    question_id = make_question()
    bad = {"text": "Updated", "options": ["A", "B"], "answer": "Z"}
    response = app.test_client().put(f"/api/questions/{question_id}", json=bad)
    assert response.status_code == 400
    delete_question_if_present(question_id)


def test_update_missing_question_returns_404():
    changed = {"text": "Updated", "options": ["A", "B"], "answer": "A"}
    response = app.test_client().put("/api/questions/99999", json=changed)
    assert response.status_code == 404

def test_delete_question_removes_it():
    question_id = make_question()
    response = app.test_client().delete(f"/api/questions/{question_id}")
    assert response.status_code == 204
    with app.app_context():
        assert db.session.get(Question, question_id) is None


def test_delete_missing_question_returns_404():
    response = app.test_client().delete("/api/questions/99999")
    assert response.status_code == 404

def test_search_questions_by_keyword():
    response = app.test_client().get("/api/questions?search=planet")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 1
    assert all("planet" in q["text"].lower() for q in data)


def test_search_questions_by_category():
    with app.app_context():
        q = Question(text="Which tool runs our pipeline?",
                     options=["GitHub Actions", "Excel"],
                     answer="GitHub Actions", category="DevOps")
        db.session.add(q)
        db.session.commit()
        question_id = q.id
    response = app.test_client().get("/api/questions?category=DevOps")
    data = response.get_json()
    assert [q["id"] for q in data] == [question_id]
    delete_question_if_present(question_id)            