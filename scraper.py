#!/usr/bin/env python3
import argparse
import json
import os
import sys
import datetime
import re
from typing import Dict, Any, Optional, List, Tuple

from bs4 import BeautifulSoup
from loguru import logger
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import numpy as np
from playwright.sync_api import sync_playwright, TimeoutError
from tabulate import tabulate

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
)
logger.add(
    "scraper.log", format="{time} | {level} | {message}", level="INFO", rotation="1 MB"
)


def scrape_timetable(html_content: str) -> Dict[str, Any]:
    """Parses HTML and extracts timetable data into structured JSON."""
    soup = BeautifulSoup(html_content, "html.parser")
    timetable_table = soup.find("table", {"id": "MainContent_StudentTimetableGridView"})

    if not timetable_table:
        logger.error(
            "❌ Timetable table not found in the HTML content! Check the screenshots folder for error details."
        )
        return {"error": "Timetable table not found in the HTML content"}

    try:
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
                        "course_code": cell_content[1]
                        if len(cell_content) > 1
                        else None,
                        "lecturer": cell_content[2] if len(cell_content) > 2 else None,
                        "room": cell_content[3] if len(cell_content) > 3 else None,
                        "weeks": cell_content[4] if len(cell_content) > 4 else None,
                    }
                    timetable[headers[day_index]].append(entry)

        logger.success("✅ Timetable successfully parsed.")
        return timetable
    except Exception as e:
        logger.error(f"❌ Failed to parse timetable HTML: {str(e)}")
        return {"error": f"Failed to parse timetable HTML: {str(e)}"}


def ensure_screenshot_dir():
    """Ensure screenshots directory exists."""
    screenshot_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "screenshots"
    )
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)
    return screenshot_dir


def save_error_screenshot(page, error_type):
    """Save a screenshot when an error occurs."""
    screenshot_dir = ensure_screenshot_dir()
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{screenshot_dir}/error_{error_type}_{timestamp}.png"
    try:
        page.screenshot(path=filename)
        logger.info(f"📸 Error screenshot saved to {filename}")
        return filename
    except Exception as e:
        logger.error(f"❌ Failed to save screenshot: {str(e)}")
        return None




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
                day_data.append(
                    [
                        event["time"],
                        event["course_code"] or "",
                        event["lecturer"] or "",
                        event["room"] or "",
                        event["weeks"] or "",
                    ]
                )

            if day_data:
                print(f"\n=== {day} ===")
                print(
                    tabulate(
                        day_data,
                        headers=["Time", "Course", "Lecturer", "Room", "Weeks"],
                        tablefmt="grid",
                    )
                )
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


def generate_timetable_image(
    timetable: Dict[str, Any], 
    output_file: str, 
    theme: str = "light"
) -> None:
    """
    Generate a visual timetable using matplotlib and save as PNG.
    
    Args:
        timetable: Dictionary containing timetable data
        output_file: Path to save the output image
        theme: 'light' or 'dark' for different visual styles
    """
    try:
        # Get all days with events
        days = [day for day, events in timetable.items() if events]

        if not days:
            logger.error("❌ No days with events found in timetable")
            return

        # Set up theme styles
        if theme == "dark":
            plt.style.use('dark_background')
            grid_color = '#555555'
            text_color = 'white'
            border_color = '#888888'
            title_color = '#ffffff'
            # Use more vibrant colors for dark theme
            colors = [
                "#5DA5DA", "#FAA43A", "#60BD68", 
                "#F17CB0", "#B2912F", "#B276B2", 
                "#DECF3F", "#F15854", "#4D4D4D"
            ]
            base_alpha = 0.8
            edge_alpha = 1.0
            background_color = '#2E2E2E'
            
            # Create custom dark theme figure
            fig = plt.figure(figsize=(14, 10), facecolor=background_color)
            ax = fig.add_subplot(111, facecolor=background_color)
        else:  # light theme
            plt.style.use('default')
            grid_color = '#cccccc'
            text_color = 'black'
            border_color = '#333333'
            title_color = '#333333'
            # Use softer colors for light theme
            colors = [
                "#8DD3C7", "#FFFFB3", "#BEBADA", 
                "#FB8072", "#80B1D3", "#FDB462", 
                "#B3DE69", "#FCCDE5", "#D9D9D9"
            ]
            base_alpha = 0.7
            edge_alpha = 0.9
            background_color = '#ffffff'
            
            # Create custom light theme figure
            fig = plt.figure(figsize=(14, 10), facecolor=background_color)
            ax = fig.add_subplot(111, facecolor=background_color)

        # Limit time range to 9:00 - 18:00 as requested
        time_range = np.arange(9, 18.25, 0.25)  # 15-minute intervals
        hour_ticks = np.arange(9, 18.25, 1)  # Hour ticks

        # Track room names and assign colors
        rooms = {}
        current_color = 0

        # Process each day and its events
        for day_index, day in enumerate(days):
            events = timetable[day]
            for event in events:
                # Skip empty events
                if not event.get("course_code"):
                    continue

                # Extract time information
                time_str = event["time"]
                time_match = re.match(
                    r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})", time_str
                )
                if not time_match:
                    logger.warning(f"⚠️ Could not parse time format: {time_str}")
                    continue

                start_hour, start_minute, end_hour, end_minute = map(
                    int, time_match.groups()
                )
                start_time = start_hour + start_minute / 60
                end_time = end_hour + end_minute / 60
                
                # Skip events outside our time range
                if end_time < 9 or start_time > 18:
                    continue

                # Clip events to our time range
                start_time = max(start_time, 9)
                end_time = min(end_time, 18)

                # Get room and assign color if new
                room = event.get("room", "Unknown")
                if room not in rooms:
                    rooms[room] = colors[current_color % len(colors)]
                    current_color += 1

                color = rooms[room]

                # Plot the event with rounded corners using custom patches
                from matplotlib.patches import FancyBboxPatch
                
                rect = FancyBboxPatch(
                    (day_index - 0.4, start_time),
                    0.8, end_time - start_time,
                    boxstyle=f"round,pad=0.02,rounding_size=0.05",
                    facecolor=color,
                    edgecolor=border_color,
                    linewidth=1.5,
                    alpha=base_alpha,
                )
                ax.add_patch(rect)

                # Add course code with better text placement
                ax.text(
                    day_index,
                    (start_time + end_time) / 2 - 0.15,
                    event["course_code"],
                    ha="center",
                    va="center",
                    fontsize=10,
                    fontweight="bold",
                    color=text_color,
                    bbox=dict(
                        facecolor='none', 
                        edgecolor='none', 
                        boxstyle='round,pad=0.2'
                    )
                )

                # Add room with better text placement
                if room != "Unknown":
                    ax.text(
                        day_index,
                        (start_time + end_time) / 2 + 0.15,
                        room,
                        ha="center",
                        va="center",
                        fontsize=9,
                        color=text_color,
                        bbox=dict(
                            facecolor='none', 
                            edgecolor='none', 
                            boxstyle='round,pad=0.2'
                        )
                    )

                # Add time label inside the box at the top
                ax.text(
                    day_index,
                    start_time + 0.1,
                    f"{start_hour:02d}:{start_minute:02d}",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color=text_color,
                    bbox=dict(
                        facecolor='none', 
                        edgecolor='none', 
                        boxstyle='round,pad=0.1'
                    )
                )

        # Set up axes and labels
        ax.set_ylim(18, 9)  # Reverse y-axis to have earlier times at the top
        ax.set_xlim(-0.8, len(days) - 0.2)
        
        # Custom x-ticks with day labels
        ax.set_xticks(range(len(days)))
        ax.set_xticklabels(days, fontsize=11, fontweight='bold', color=text_color)
        
        # Custom y-ticks for hours (9:00 - 18:00) with better formatting
        ax.set_yticks(hour_ticks)
        ax.set_yticklabels([f"{int(h):02d}:00" for h in hour_ticks], fontsize=10, color=text_color)
        
        # Additional minor ticks for 30-minute intervals
        minor_ticks = np.arange(9, 18, 0.5)
        ax.set_yticks(minor_ticks, minor=True)
        
        # Labels and title with improved styling
        ax.set_ylabel("Time", fontsize=12, fontweight='bold', color=text_color)
        
        # Add grid with custom appearance
        ax.grid(which='major', axis='y', linestyle='-', linewidth=0.8, color=grid_color, alpha=0.8)
        ax.grid(which='minor', axis='y', linestyle='--', linewidth=0.5, color=grid_color, alpha=0.5)
        
        # Add horizontal lines for each hour to improve readability
        for hour in hour_ticks:
            ax.axhline(y=hour, color=grid_color, linestyle='-', linewidth=0.8, alpha=0.6)
        
        # Add vertical lines between days
        for day_idx in range(len(days)-1):
            ax.axvline(x=day_idx+0.5, color=grid_color, linestyle='-', linewidth=0.8, alpha=0.4)

        # Create a custom legend for rooms
        from matplotlib.patches import Patch
        legend_elements = []
        for room, color in rooms.items():
            legend_elements.append(
                Patch(facecolor=color, edgecolor=border_color, alpha=base_alpha, label=room)
            )

        # Place the legend outside the main plot
        ax.legend(
            handles=legend_elements,
            title="Room Legend",
            title_fontsize=11,
            fontsize=9,
            loc='upper center',
            bbox_to_anchor=(0.5, -0.05),
            ncol=min(5, len(rooms)),
            framealpha=0.8,
            edgecolor=border_color,
        )

        # Add a descriptive title with improved styling
        mode_text = "Dark Mode" if theme == "dark" else "Light Mode"
        plt.title(f"Weekly Timetable - {mode_text}", fontsize=16, fontweight='bold', color=title_color, pad=15)
        
        # Add date/time info in the corner
        current_time = datetime.datetime.now().strftime("%Y-%m-%d")
        ax.text(
            0.99, 0.01, f"Generated: {current_time}", 
            transform=ax.transAxes, fontsize=8, 
            color=text_color, alpha=0.7,
            ha='right', va='bottom'
        )
        
        # Adjust layout
        plt.tight_layout(pad=2.5)
        
        # Save the figure with higher resolution
        plt.savefig(f"{os.path.splitext(output_file)[0]}_{theme}.png", dpi=300, bbox_inches='tight')
        logger.success(f"✅ Timetable image saved as {os.path.splitext(output_file)[0]}_{theme}.png")
        
        # Close the figure
        plt.close(fig)
        
        # If this is the first run (light theme), also generate dark theme
        if theme == "light":
            generate_timetable_image(timetable, output_file, theme="dark")
            
    except Exception as e:
        logger.error(f"❌ Failed to generate timetable image: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description="UL Timetable Scraper - Fetch your University of Limerick timetable."
    )
    parser.add_argument("-u", "--username", help="Your UL student email")
    parser.add_argument("-p", "--password", help="Your UL password")
    parser.add_argument("-o", "--output", help="Save timetable to a JSON file")
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "table"],
        default="json",
        help="Output format: json or table (default: json)",
    )
    parser.add_argument(
        "--image",
        help="Generate and save a timetable visualization as PNG images",
        metavar="IMAGE_PATH",
    )
    parser.add_argument(
        "--theme",
        choices=["light", "dark", "both"],
        default="both",
        help="Theme for timetable visualization: light, dark, or both (default: both)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in visible mode (not headless)",
    )
    parser.add_argument(
        "--slow-mo",
        type=int,
        default=2000,
        help="Slow motion delay in milliseconds for browser actions (default: 2000)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase logging verbosity"
    )

    args = parser.parse_args()

    # Set logging level based on verbosity
    if args.verbose:
        logger.remove()
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level="DEBUG",
        )
        logger.add(
            "scraper.log",
            format="{time} | {level} | {message}",
            level="DEBUG",
            rotation="1 MB",
        )

    # Ensure screenshots directory exists
    ensure_screenshot_dir()

    # Handle credential input - check args, then environment variables, then prompt
    username = args.username or os.environ.get("UL_USERNAME")
    password = args.password or os.environ.get("UL_PASSWORD")

    if not username:
        username = input("Enter your UL student email: ")

    if not password:
        import getpass

        password = getpass.getpass("Enter your UL password: ")

    # Run the scraper
    logger.info(f"🔍 Starting timetable scraping with slow_mo={args.slow_mo}ms")
    
    # Launch browser with specified slow_mo value
    with sync_playwright() as p:
        # Use the slow_mo value from args
        browser = p.chromium.launch(headless=not args.no_headless, slow_mo=args.slow_mo)
        page = browser.new_page()

        try:
            logger.info(f"🔗 Logging in for user: {username}")
            page.goto(
                "https://www.timetable.ul.ie/Login.aspx?ReturnUrl=%2fUA%2fDefault.aspx"
            )
            
            # Wait for page to be fully loaded
            page.wait_for_load_state("networkidle")

            try:
                username_field = page.get_by_role("textbox", name="Username")
                # Ensure element is visible and stable before interaction
                username_field.wait_for(state="visible")
                username_field.fill(username)
            except Exception as e:
                screenshot_path = save_error_screenshot(page, "username_field")
                logger.error(
                    f"❌ Cannot find or interact with Username field: {str(e)}"
                )
                browser.close()
                return 1

            try:
                password_field = page.get_by_role("textbox", name="Password")
                password_field.wait_for(state="visible")
                password_field.fill(password)
            except Exception as e:
                screenshot_path = save_error_screenshot(page, "password_field")
                logger.error(
                    f"❌ Cannot find or interact with Password field: {str(e)}"
                )
                browser.close()
                return 1

            try:
                login_button = page.get_by_role("button", name="Login")
                login_button.wait_for(state="visible")
                login_button.click()
                # Wait for navigation after login
                page.wait_for_load_state("networkidle")
            except Exception as e:
                screenshot_path = save_error_screenshot(page, "login_button")
                logger.error(f"❌ Cannot find or click Login button: {str(e)}")
                browser.close()
                return 1

            try:
                # Give some time for the dashboard to fully load
                page.wait_for_timeout(1500)
                timetable_link = page.get_by_role(
                    "link", name="Card image cap Student Timetable", exact=True
                )
                timetable_link.wait_for(state="visible")
                timetable_link.click()
                # Wait for navigation to complete
                page.wait_for_load_state("networkidle")
            except Exception as e:
                screenshot_path = save_error_screenshot(page, "timetable_link")
                logger.error(
                    f"❌ Cannot find or click Student Timetable link: {str(e)}"
                )
                browser.close()
                return 1

            logger.info("🔄 Navigating to Student Timetable page...")
            
            # Ensure timetable is fully loaded before capturing content
            page.wait_for_timeout(2000)
            html_content = page.content()
            logger.success("✅ Successfully retrieved timetable HTML.")
            
            # Parse the timetable
            timetable = scrape_timetable(html_content)

        except TimeoutError as e:
            screenshot_path = save_error_screenshot(page, "timeout")
            logger.error(f"⏳ Timeout error: {str(e)}")
            browser.close()
            return 1
        except Exception as e:
            screenshot_path = save_error_screenshot(page, "unexpected")
            logger.error(f"❌ Unexpected error: {str(e)}")
            browser.close()
            return 1

        browser.close()

    if "error" in timetable:
        logger.error(f"❌ {timetable['error']}")
        print(f"Error: {timetable['error']}")
        print("Check screenshots directory and logs for more details.")
        return 1

    # Save to file if requested
    if args.output:
        save_timetable(timetable, args.output)

    # Generate image if requested
    if args.image:
        logger.info(f"🎨 Generating timetable visualization(s) with theme: {args.theme}")
        if args.theme == "both":
            # Both themes will be generated by default when calling with "light"
            generate_timetable_image(timetable, args.image, theme="light")
        else:
            # Generate only the specified theme
            generate_timetable_image(timetable, args.image, theme=args.theme)

    # Display the timetable
    display_timetable(timetable, args.format)
    
    logger.success("✅ Timetable processing completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
