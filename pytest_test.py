import pytest
import os
from bs4 import BeautifulSoup
from scraper import scrape_timetable, scrape_timetable_for_user
from datetime import datetime

def test_scrape_timetable():
    """Test the HTML parsing function with a minimal HTML sample."""
    # Create a simple timetable HTML structure
    html = """
    <table id="MainContent_StudentTimetableGridView">
        <tr>
            <th>Monday</th>
            <th>Tuesday</th>
        </tr>
        <tr>
            <td>9:00 - 10:00<br>CS101<br>Dr. Smith<br>Room A1<br>Weeks 1-12</td>
            <td>11:00 - 12:00<br>CS102<br>Dr. Jones<br>Room B2<br>Weeks 1-12</td>
        </tr>
    </table>
    """
    
    # Parse the HTML
    result = scrape_timetable(html)
    
    # Check the structure and content
    assert isinstance(result, dict)
    assert "Monday" in result
    assert "Tuesday" in result
    assert len(result["Monday"]) == 1
    assert result["Monday"][0]["time"] == "9:00 - 10:00"
    assert result["Monday"][0]["course_code"] == "CS101"
    assert result["Monday"][0]["lecturer"] == "Dr. Smith"
    assert result["Monday"][0]["room"] == "Room A1"
    assert result["Monday"][0]["weeks"] == "Weeks 1-12"

def test_mock_scrape_timetable_for_user():
    """
    Test the scrape_timetable_for_user function with mock credentials.
    This test will return early due to login failure, but we can check 
    that the function handles errors properly.
    """
    # Call with mock credentials (this will fail to login but should return a dict with error)
    result = scrape_timetable_for_user("mock_user", "mock_pass", headless=True)
    
    # Check the result structure
    assert isinstance(result, dict)
    # Should have an error key since the credentials are not valid
    assert "error" in result
