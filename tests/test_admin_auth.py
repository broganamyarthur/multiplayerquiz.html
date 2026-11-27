from app import app
from conftest import TEST_ADMIN_PASSWORD


def test_sign_in_with_correct_password_succeeds():
    client = app.test_client()
    response = client.post("/api/login", json={"password": TEST_ADMIN_PASSWORD})
    assert response.status_code == 200


def test_sign_in_with_wrong_password_is_refused():
    client = app.test_client()
    response = client.post("/api/login", json={"password": "wrong"})
    assert response.status_code == 401