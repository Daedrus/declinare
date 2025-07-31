import os
import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.secret_key = "test"
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["lang"] = "sv"
        yield client

def test_quiz_page_loads(client):
    response = client.get("/quiz")
    assert response.status_code == 200
    assert b"Noun Quiz" in response.data

def test_submit_without_quiz_redirects(client):
    response = client.post("/submit", data={"user_answer": "dummy"}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/quiz")

def test_correct_answers_set_streak(client):
    # First load quiz and grab session
    client.get("/quiz")
    with client.session_transaction() as sess:
        quiz = sess["quiz"]
        correct = quiz["correct_answer"]

    # Submit correct answer
    response = client.post("/submit", data={"user_answer": correct})
    assert b"Correct" in response.data

    # Repeat one more time
    client.get("/quiz")
    with client.session_transaction() as sess:
        quiz = sess["quiz"]
        correct = quiz["correct_answer"]

    response = client.post("/submit", data={"user_answer": correct})
    assert b"Correct" in response.data

    # Check streak is updated
    with client.session_transaction() as sess:
        assert sess["streak"] == 2

def test_streak_resets_on_wrong_answer(client):
    # Load quiz
    client.get("/quiz")
    with client.session_transaction() as sess:
        sess["streak"] = 2

    # Submit wrong answer
    client.post("/submit", data={"user_answer": "totallywrong"})
    with client.session_transaction() as sess:
        assert sess["streak"] == 0

def test_language_switch_resets_streak(client):
    with client.session_transaction() as sess:
        sess["streak"] = 3
        sess["lang"] = "sv"

    client.get("/quiz?lang=ro")
    with client.session_transaction() as sess:
        assert sess["lang"] == "ro"
        assert sess["streak"] == 0
