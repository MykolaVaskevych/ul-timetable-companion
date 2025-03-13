from setuptools import setup

setup(
    name="ul-timetable-scraper",
    version="0.1.0",
    py_modules=["scraper"],
    install_requires=[
        "beautifulsoup4>=4.13.0",
        "cryptography>=44.0.0",
        "loguru>=0.7.0",
        "playwright>=1.50.0",
        "tabulate>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "ul-timetable=scraper:main",
        ],
    },
)