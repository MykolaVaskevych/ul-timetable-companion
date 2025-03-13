# UL Timetable Scraper

A command-line tool to fetch and display University of Limerick timetables.

## Features

- Scrapes timetable data from the UL timetable website
- Display timetable in JSON or tabular format
- Save timetable to a JSON file
- Interactive credential input or command-line options

## Installation

### Prerequisites

- Python 3.9 or higher
- pip or another Python package manager

### Installation Steps

1. Clone this repository:

```bash
git clone https://github.com/yourusername/ul-timetable-scraper.git
cd ul-timetable-scraper
```

2. Install the package in development mode:

```bash
pip install -e .
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

# Run with browser visible (not headless)
ul-timetable --no-headless

# Get verbose logging
ul-timetable -v
```

### Command-line options:

```
-u, --username    Your UL student email
-p, --password    Your UL password
-o, --output      Save timetable to a JSON file
-f, --format      Output format: json or table (default: json)
--no-headless     Run browser in visible mode (not headless)
-v, --verbose     Increase logging verbosity
```

## Security Notes

- Your credentials are never stored persistently
- Password input is masked when entered interactively
- Consider using environment variables for sensitive credentials:

```bash
export UL_USERNAME="your.email@studentmail.ul.ie"
export UL_PASSWORD="yourpassword"
ul-timetable -u "$UL_USERNAME" -p "$UL_PASSWORD"
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

# Install dependencies
pip install -e .
```

### Testing

Tests are written using pytest:

```bash
pytest
```