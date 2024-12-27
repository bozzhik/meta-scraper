import os
import json
import requests
from bs4 import BeautifulSoup
import unicodedata
from datetime import datetime
from collections import Counter
from urllib.parse import urlparse
import re

OUTPUT_FOLDER = "output"
PARTISANS_FOLDER = os.path.join(OUTPUT_FOLDER, "partisans")
WEBSITES_FILE = "websites.json"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PARTISANS_FOLDER, exist_ok=True)

def load_websites(file_path):
    """Loads website URLs from a JSON file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("urls", []), data.get("partisans_urls", [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {file_path}: {e}")
        return [], []

def fetch_metadata(url):
    """Fetches metadata and performs additional analysis."""
    no_data = "— — —"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Metadata
        metadata = {
            "url": url,
            "title": (soup.title.string.strip() if soup.title else no_data),
            "description": (soup.find("meta", attrs={"name": "description"}) or {}).get("content", no_data).strip(),
            "keywords": (soup.find("meta", attrs={"name": "keywords"}) or {}).get("content", no_data).strip(),
            "author": (soup.find("meta", attrs={"name": "author"}) or {}).get("content", no_data).strip(),
        }

        # Open Graph Tags
        metadata["og_title"] = (soup.find("meta", attrs={"property": "og:title"}) or {}).get("content", no_data).strip()
        metadata["og_description"] = (soup.find("meta", attrs={"property": "og:description"}) or {}).get("content", no_data).strip()
        metadata["og_image"] = (soup.find("meta", attrs={"property": "og:image"}) or {}).get("content", no_data).strip()
        metadata["canonical"] = (soup.find("link", attrs={"rel": "canonical"}) or {}).get("href", no_data).strip()

        # Text Analysis
        visible_text = " ".join([text for text in soup.stripped_strings])
        words = re.findall(r'\w+', visible_text.lower())
        word_counts = Counter(words)
        stopwords = set(["and", "the", "a", "to", "of", "in", "is", "it", "you", "that", "on", "for", "with", "as", "at", "this", "by", "an", "be", "are", "or", "was", "but"])
        filtered_words = [word for word in words if word not in stopwords]
        metadata["top_words"] = dict(word_counts.most_common(20))

        # Images
        metadata["images"] = [img["src"] for img in soup.find_all("img", src=True)]

        # Links
        links = [a["href"] for a in soup.find_all("a", href=True)]
        parsed_url = urlparse(url)
        metadata["internal_links"] = [link for link in links if parsed_url.netloc in link or link.startswith("/")]
        metadata["external_links"] = [link for link in links if parsed_url.netloc not in link and not link.startswith("/")]

        return {k: unicodedata.normalize("NFKC", v) if isinstance(v, str) else v for k, v in metadata.items()}
    except requests.RequestException as e:
        print(f"Error fetching metadata for {url}: {e}")
        return None

def save_metadata(metadata, folder):
    """Saves metadata to an .md file."""
    timestamp = datetime.now().strftime("%Y%m%d")
    file_name = os.path.join(folder, f"{timestamp}_{metadata['url'].replace('http://', '').replace('https://', '').replace('/', '_')}.md")
    
    domain = metadata["url"].rstrip("/")

    try:
        with open(file_name, "w", encoding="utf-8") as md_file:
            md_file.write(f"# {metadata['url']}\n\n")

            # Title
            if metadata["title"] != metadata.get("og_title", ""):
                md_file.write(f"**Title:** {metadata['title']}\n\n")
            else:
                md_file.write(f"**Title:** {metadata['title']}\n\n")

            # Description
            if metadata["description"] != metadata.get("og_description", ""):
                md_file.write(f"**Description:** {metadata['description']}\n\n")
            else:
                md_file.write(f"**Description:** {metadata['description']}\n\n")

            # Keywords and Author
            md_file.write(f"**Keywords:** {metadata.get('keywords', '— — —')}\n\n")
            md_file.write(f"**Author:** {metadata.get('author', '— — —')}\n\n")

            # Open Graph Image as Markdown Image (with fixed width)
            og_image = metadata.get("og_image", "")
            if og_image and og_image != "— — —":
                if og_image.startswith("/"):  # Add domain for relative paths
                    og_image = f"{domain}{og_image}"
                md_file.write(f'<img src="{og_image}" alt="OG Image" width="500px">\n\n')

            # Top Words in a Table
            top_words = metadata.get("top_words", {})
            if top_words:
                md_file.write("**Top Words:**\n\n| Word       | Count |\n|------------|-------|\n")
                md_file.writelines(f"| {word:<10} | {count:<5} |\n" for word, count in top_words.items())
                md_file.write("\n\n")

            # External Links (excluding links matching the domain or invalid links)
            external_links = metadata.get("external_links", [])
            filtered_external_links = [
                link for link in external_links 
                if not link.startswith(domain) and not link.startswith("#") and not link.startswith("tel:")
            ]
            if filtered_external_links:
                md_file.write("**External links:**\n\n")
                for link in filtered_external_links:
                    md_file.write(f"- {link}\n")
                md_file.write("\n")

        print(f"Saved to [{file_name}]")
    except Exception as e:
        print(f"Error saving metadata for {metadata['url']}: {e}")

def process_urls(urls, folder):
    """Processes a list of URLs and saves their metadata to the specified folder."""
    for site in urls:
        print(f"Fetching metadata for: {site}")
        metadata = fetch_metadata(site)
        if metadata is None:
            print(f"Skipping {site}: Unable to fetch metadata (URL might be invalid or inaccessible).")
        else:
            save_metadata(metadata, folder)

if __name__ == "__main__":
    websites, partisans_urls = load_websites(WEBSITES_FILE)

    if not websites and not partisans_urls:
        print(f"No websites or partisans URLs found in {WEBSITES_FILE}. Please add URLs to the file.")
    else:
        if websites:
            process_urls(websites, OUTPUT_FOLDER)

        if partisans_urls:
            process_urls(partisans_urls, PARTISANS_FOLDER)
