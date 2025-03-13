# UL Timetable Scraper

A command-line tool to fetch and display University of Limerick timetables with beautiful visualizations.

## Features

- Scrapes timetable data from the UL timetable website
- Display timetable in JSON or tabular format
- Save timetable to a JSON file
- Generate beautiful visual timetable as PNG images (light and dark mode)
- Interactive credential input or command-line options
- Robust page loading with configurable timeouts

## Installation

### Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) - A faster, more reliable Python package installer and resolver

### Installation Steps

1. Clone this repository:

```bash
git clone https://github.com/yourusername/ul-timetable-scraper.git
cd ul-timetable-scraper
```

2. Install the package in development mode:

```bash
uv sync -e .
```

3. Install Playwright browser dependencies:

```bash
python -m playwright install chromium
```

## Usage

### Basic usage:

```bash
# Run with interactive prompts for credentials
ul-timetable

# Provide credentials via command line
ul-timetable -u "your.email@studentmail.ul.ie" -p "yourpassword"

# Display timetable in tabular format
ul-timetable -f table

# Save timetable to a JSON file
ul-timetable -o timetable.json

# Generate visual timetable images (both light and dark mode)
ul-timetable --image timetable.png

# Generate only light mode timetable image
ul-timetable --image timetable.png --theme light

# Generate only dark mode timetable image
ul-timetable --image timetable.png --theme dark

# Run with browser visible (not headless)
ul-timetable --no-headless

# Increase slow motion timing for better stability
ul-timetable --slow-mo 3000

# Get verbose logging
ul-timetable -v
```

### Command-line options:

```
-u, --username    Your UL student email
-p, --password    Your UL password
-o, --output      Save timetable to a JSON file
-f, --format      Output format: json or table (default: json)
--image           Generate and save timetable visualization as PNG images
--theme           Theme for visualization: light, dark, or both (default: both)
--no-headless     Run browser in visible mode (not headless)
--slow-mo         Slow motion delay in milliseconds (default: 2000)
-v, --verbose     Increase logging verbosity
```

## Visual Timetable

The tool can generate beautiful visual representations of your timetable as PNG images in both light and dark modes:

```bash
# Generate timetable images in both light and dark modes
ul-timetable --image timetable.png
```

This creates clear, visually appealing, color-coded visualizations of your schedule with the following features:

- Each day of the week is displayed along the X-axis
- Times run vertically along the Y-axis (focused on 9:00-18:00 range)
- Events are color-coded by room with a visually pleasing color palette
- Course codes, room numbers, and time labels are clearly displayed
- Grid lines make it easy to identify class times
- Beautiful rounded corners on event boxes
- Both light and dark mode themes for different preferences
- Higher resolution output (300 DPI) for better clarity

## Security Notes

- Your credentials are never stored persistently
- Password input is masked when entered interactively
- Consider using environment variables for sensitive credentials:

```bash
export UL_USERNAME="your.email@studentmail.ul.ie"
export UL_PASSWORD="yourpassword"
ul-timetable
```

## Development

### Setting up a development environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies using uv
uv sync -e .
```

### Testing

Tests are written using pytest:

```bash
pytest
```

## Troubleshooting

If the scraper fails to retrieve data:

1. Try increasing the slow motion delay:
   ```
   ul-timetable --slow-mo 3000
   ```

2. Use the visible browser mode to see what's happening:
   ```
   ul-timetable --no-headless
   ```

3. Check the screenshots folder for error screenshots
   ```
   ls screenshots/
   ```

4. Enable verbose logging for more details:
   ```
   ul-timetable -v
   ```