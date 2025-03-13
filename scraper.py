#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import Dict, Any, Optional

from bs4 import BeautifulSoup
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError
from tabulate import tabulate

# Configure logging
logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="INFO")
logger.add("scraper.log", format="{time} | {level} | {message}", level="INFO", rotation="1 MB")


def scrape_timetable(html_content: str) -> Dict[str, Any]:
    """Parses HTML and extracts timetable data into structured JSON."""
    soup = BeautifulSoup(html_content, "html.parser")
    timetable_table = soup.find("table", {"id": "MainContent_StudentTimetableGridView"})

    if not timetable_table:
        logger.error("❌ Timetable table not found!")
        return {}

    headers = [th.get_text(strip=True) for th in timetable_table.find_all("th")]
    timetable = {day: [] for day in headers}
    rows = timetable_table.find_all("tr")[1:]

    for row in rows:
        cells = row.find_all("td")
        for day_index, cell in enumerate(cells):
            cell_content = list(cell.stripped_strings)
            if cell_content:
                entry = {
                    "time": cell_content[0],
                    "course_code": cell_content[1] if len(cell_content) > 1 else None,
                    "lecturer": cell_content[2] if len(cell_content) > 2 else None,
                    "room": cell_content[3] if len(cell_content) > 3 else None,
                    "weeks": cell_content[4] if len(cell_content) > 4 else None,
                }
                timetable[headers[day_index]].append(entry)

    logger.success("✅ Timetable successfully parsed.")
    return timetable


def scrape_timetable_for_user(login: str, password: str, headless: bool = True) -> Dict[str, Any]:
    """Logs into the UL timetable website, scrapes the timetable HTML, and returns parsed data."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        try:
            logger.info(f"🔗 Logging in for user: {login}")
            page.goto("https://www.timetable.ul.ie/Login.aspx?ReturnUrl=%2fUA%2fDefault.aspx")

            page.get_by_role("textbox", name="Username").fill(login)
            page.get_by_role("textbox", name="Password").fill(password)
            page.get_by_role("button", name="Login").click()
            page.get_by_role("link", name="Card image cap Student Timetable", exact=True).click()

            logger.info("🔄 Navigating to Student Timetable page...")
            page.wait_for_selector("table#MainContent_StudentTimetableGridView", timeout=10000)

            html_content = page.content()
            logger.success("✅ Successfully retrieved timetable HTML.")

        except TimeoutError as e:
            logger.error(f"⏳ Timeout error: {str(e)}")
            browser.close()
            return {"error": "Timeout while scraping timetable."}
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            browser.close()
            return {"error": "Failed to scrape timetable."}

        browser.close()
        return scrape_timetable(html_content)


def display_timetable(timetable: Dict[str, Any], format_type: str = "json") -> None:
    """Display the timetable in the specified format."""
    if format_type == "json":
        print(json.dumps(timetable, indent=4))
    elif format_type == "table":
        # Format data for tabulate
        tables = []
        for day, events in timetable.items():
            if not events:
                continue
                
            day_data = []
            for event in events:
                day_data.append([
                    event["time"],
                    event["course_code"] or "",
                    event["lecturer"] or "",
                    event["room"] or "",
                    event["weeks"] or "",
                ])
            
            if day_data:
                print(f"\n=== {day} ===")
                print(tabulate(
                    day_data,
                    headers=["Time", "Course", "Lecturer", "Room", "Weeks"],
                    tablefmt="grid"
                ))
    else:
        logger.error(f"Unknown format type: {format_type}")


def save_timetable(timetable: Dict[str, Any], output_file: str) -> None:
    """Save the timetable to a file."""
    try:
        with open(output_file, "w") as f:
            json.dump(timetable, f, indent=4)
        logger.success(f"✅ Timetable saved to {output_file}")
    except Exception as e:
        logger.error(f"❌ Failed to save timetable: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description="UL Timetable Scraper - Fetch your University of Limerick timetable."
    )
    parser.add_argument("-u", "--username", help="Your UL student email")
    parser.add_argument("-p", "--password", help="Your UL password")
    parser.add_argument(
        "-o", "--output", help="Save timetable to a JSON file"
    )
    parser.add_argument(
        "-f", "--format", choices=["json", "table"], default="json",
        help="Output format: json or table (default: json)"
    )
    parser.add_argument(
        "--no-headless", action="store_true",
        help="Run browser in visible mode (not headless)"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Increase logging verbosity"
    )
    
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="DEBUG")
        logger.add("scraper.log", format="{time} | {level} | {message}", level="DEBUG", rotation="1 MB")
    
    # Handle credential input - check args, then environment variables, then prompt
    username = args.username or os.environ.get("UL_USERNAME")
    password = args.password or os.environ.get("UL_PASSWORD")
    
    if not username:
        username = input("Enter your UL student email: ")
    
    if not password:
        import getpass
        password = getpass.getpass("Enter your UL password: ")
    
    # Run the scraper
    timetable = scrape_timetable_for_user(username, password, headless=not args.no_headless)
    
    if "error" in timetable:
        logger.error(f"❌ {timetable['error']}")
        return 1
    
    # Save to file if requested
    if args.output:
        save_timetable(timetable, args.output)
    
    # Display the timetable
    display_timetable(timetable, args.format)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())