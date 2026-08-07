import pytest
from app import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def test_home_page_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Quiz App' in response.data or b'Welcome' in response.data


def test_health_endpoint(client):
    response = client.get('/healthz')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}


def test_submit_route_returns_score_page(client):
    response = client.post('/submit', data={
        'q0': '1989',
        'q1': 'Mars',
        'q2': 'Ernest Hemingway'
    })
    assert response.status_code == 200
    assert b'Your Score' in response.data or b'Fantastic performance!' in response.data
