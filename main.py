import os
import json
import requests
from bs4 import BeautifulSoup
import unicodedata
from datetime import datetime

OUTPUT_FOLDER = "output"
WEBSITES_FILE = "websites.json"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def load_websites(file_path):
    """Loads website URLs from a JSON file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f).get("urls", [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {file_path}: {e}")
        return []

def fetch_metadata(url):
    """Fetches metadata from a given URL."""
    no_data = "— — —"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        metadata = {
            "url": url,
            "title": (soup.title.string.strip() if soup.title else no_data),
            "description": (soup.find("meta", attrs={"name": "description"}) or {}).get("content", no_data).strip(),
            "keywords": (soup.find("meta", attrs={"name": "keywords"}) or {}).get("content", no_data).strip(),
            "author": (soup.find("meta", attrs={"name": "author"}) or {}).get("content", no_data).strip(),
        }

        return {k: unicodedata.normalize("NFKC", v) for k, v in metadata.items()}
    except requests.RequestException as e:
        print(f"Error fetching metadata for {url}: {e}")
        return None

def save_metadata(metadata):
    """Saves metadata to an .md file."""
    timestamp = datetime.now().strftime("%Y%m%d")
    file_name = os.path.join(OUTPUT_FOLDER, f"{timestamp}_{metadata['url'].replace('http://', '').replace('https://', '').replace('/', '_')}.md")
    try:
        with open(file_name, "w", encoding="utf-8") as md_file:
            md_file.write(f"# Metadata for {metadata['url']}\n\n")
            md_file.writelines(f"**{key.capitalize()}:** {value}\n\n" for key, value in metadata.items() if key != "url")
        print(f"Saved to [{file_name}]")
    except Exception as e:
        print(f"Error saving metadata for {metadata['url']}: {e}")

if __name__ == "__main__":
    sites = load_websites(WEBSITES_FILE)

    if not sites:
        print(f"No websites found in {WEBSITES_FILE}. Please add URLs to the file.")
    else:
        for site in sites:
            print(f"Fetching metadata for: {site}")
            metadata = fetch_metadata(site)
            if metadata is None:
                print(f"Skipping {site}: Unable to fetch metadata (URL might be invalid or inaccessible).")
            else:
                save_metadata(metadata)
