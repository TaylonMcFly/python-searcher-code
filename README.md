# Search and Open in Brave

This Python application performs search queries using multiple search engines (DuckDuckGo and Brave Search), extracts the top results, and automatically opens them in the Brave browser (Windows only).

## Features

- Search multiple engines in one query.
- Extract real URLs from redirect links.
- Limit results per engine (default 5).
- Open all results as new tabs in Brave.
- Handles HTTP errors and request timeouts.

## Requirements

- Python 3.7+
- Packages:
  - requests
  - beautifulsoup4

Install dependencies:
```bash
pip install requests beautifulsoup4
```
## Setup

Set the Brave browser executable path in the script:
```
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
```
## How It Works

1. User enters a search query.
2. Script sends the query to each search engine.
3. Parses HTML results and extracts URLs.
4. Resolves redirected URLs to real targets.
5. Prints results and opens links in Brave tabs.

## Usage

Run the script:
```bash
python tay_search.py
```
Enter your query or type выход to exit.

## Notes

- Designed for Windows Brave browser.
- User-Agent header mimics a browser to avoid blocking.
- Duplicate URLs are removed.
- Opening links waits until all are printed.

## License

Free for personal and educational use.

## Contact

For feedback or issues, open an issue in the repo.
