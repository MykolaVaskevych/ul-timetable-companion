import pytest
import requests
from scraper import scrape_timetable_for_user

@pytest.fixture
def test_scraper():
    """Test Playwright scraping with mock login credentials."""
    data = scrape_timetable_for_user("mock_user", "mock_pass")
    assert isinstance(data, dict)
    assert len(data) > 0

def test_server():
    """Test the Flask server API."""
    session_response = requests.get("http://127.0.0.1:5000/get_session_key")
    assert session_response.status_code == 200
    session_data = session_response.json()

    session_id = session_data["session_id"]
    session_key = session_data["session_key"].encode()

    # Encrypt sample login and password
    from cryptography.fernet import Fernet
    cipher = Fernet(session_key)
    enc_login = cipher.encrypt("test_user".encode()).decode()
    enc_password = cipher.encrypt("test_pass".encode()).decode()

    response = requests.post(
        "http://127.0.0.1:5000/get_timetable",
        json={"session_id": session_id, "login": enc_login, "password": enc_password},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), dict)
