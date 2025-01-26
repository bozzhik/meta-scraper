import os
import json
import requests
from bs4 import BeautifulSoup
import unicodedata
from datetime import datetime
from collections import Counter
from urllib.parse import urlparse
import re
import csv

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

        # Expanded stopwords list including common prepositions and pronouns
        stopwords = set([
            "и", "в", "на", "с", "по", "о", "из", "за", "для", "к", "от", "при",
            "что", "это", "как", "так", "но", "а", "же", "то", "у", "об", "над",
            "ли", "же", "без", "до", "под", "через", "между", "про", "вне", "поэтому",
            "мы", "я", "они", "вы", "он", "она", "его", "ее", "их", "мне", "тебе", "вас", "нас"
        ])

        # Filter out stopwords, one-letter words, and numbers
        filtered_words = [
            word for word in words
            if word not in stopwords and len(word) > 1 and not word.isdigit()
        ]
        filtered_word_counts = Counter(filtered_words)
        metadata["top_words"] = dict(filtered_word_counts.most_common(20))

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

            # External Links (excluding duplicates)
            external_links = metadata.get("external_links", [])
            unique_external_links = list(set(external_links))  # Remove duplicates
            filtered_external_links = [
                link for link in unique_external_links 
                if not link.startswith(domain) and not link.startswith("#") and not link.startswith("tel:") and link.strip()
            ]
            if filtered_external_links:
                md_file.write("**External links:**\n\n")
                for link in filtered_external_links:
                    md_file.write(f"- {link}\n")
                md_file.write("\n")

        print(f"Saved to [{file_name}]")
    except Exception as e:
        print(f"Error saving metadata for {metadata['url']}: {e}")

def save_to_csv(metadata_list, base_csv_file):
    """Saves metadata list to a CSV file with a timestamp, overwriting the previous file."""
    timestamp = datetime.now().strftime("%Y%m%d")
    csv_file = f"{base_csv_file.replace('.csv', '')}_{timestamp}.csv"

    try:
        with open(csv_file, mode="w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            # Add column headers
            writer.writerow(["url", "title", "description", "keywords", "author", "og_image", "top_words", "external_links"])
            for metadata in metadata_list:
                writer.writerow([
                    metadata["url"], metadata["title"], metadata["description"],
                    metadata["keywords"], metadata["author"], metadata["og_image"],
                    json.dumps(metadata["top_words"], ensure_ascii=False),
                    json.dumps(metadata["external_links"], ensure_ascii=False)
                ])
        print(f"Data saved to {csv_file}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def process_urls(urls, folder, csv_file):
    """Processes a list of URLs, saves metadata to the folder and CSV file."""
    metadata_list = []
    for site in urls:
        print(f"Fetching metadata for: {site}")
        metadata = fetch_metadata(site)
        if metadata is None:
            print(f"Skipping {site}: Unable to fetch metadata (URL might be invalid or inaccessible).")
        else:
            save_metadata(metadata, folder)
            metadata_list.append(metadata)
    if metadata_list:
        save_to_csv(metadata_list, csv_file)

if __name__ == "__main__":
    websites, partisans_urls = load_websites(WEBSITES_FILE)

    websites_csv = os.path.join(OUTPUT_FOLDER, "websites_metadata.csv")
    partisans_csv = os.path.join(PARTISANS_FOLDER, "partisans_metadata.csv")

    if not websites and not partisans_urls:
        print(f"No websites or partisans URLs found in {WEBSITES_FILE}. Please add URLs to the file.")
    else:
        if websites:
            process_urls(websites, OUTPUT_FOLDER, websites_csv)
        if partisans_urls:
            process_urls(partisans_urls, PARTISANS_FOLDER, partisans_csv)
