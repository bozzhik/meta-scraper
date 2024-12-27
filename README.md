# Meta Scraper: Website Metadata Extractor

**meta-scraper** is a simple Python script that automates the collection of metadata (title, description, keywords, and author) from websites. It’s useful for competitor analysis or website auditing.

## Features

- Extracts metadata from a list of websites provided in a `websites.json` file.
- Saves metadata as Markdown `.md` files in the `output` folder.
- Filenames include a timestamp (`YYYYMMDD`) for better organization.
- Gracefully handles errors for invalid or inaccessible URLs without creating unnecessary `.md` files.
- Single-file script for easy use.

## Requirements

- Python 3.12.6 or higher
- Libraries: `requests`, `beautifulsoup4`

Install the required libraries:

```bash
pip install requests beautifulsoup4
```

## Usage

1. Add websites to the `websites.json` file in the following format:

   ```json
   {
     "urls": ["https://bozzhik.com", "https://example.com"]
   }
   ```

2. Run the script:

   ```bash
   python main.py
   ```

3. Check the `output` folder for `.md` files containing the metadata. Filenames will include a timestamp (`YYYYMMDD`) followed by the website URL, e.g., `20231227_bozzhik.com.md`.

4. If a URL is invalid or inaccessible, the script will display an error message in the console but will not create an `.md` file for that URL.

## Example Output

For `https://bozzhik.com`, the output file in `output/` will look like this:

```markdown
# Metadata for https://bozzhik.com

**Title:** BOZZHIK

**Description:** I'm a website developer and user interface designer.

**Keywords:** bozzhik, bozhik, bojic, maxim bozhik, maxim bojic

**Author:** — — —
```

If the URL is invalid, the script will display:

```bash
Error fetching metadata for https://some-website.com: <error details>
Skipping https://some-website.com: Unable to fetch metadata (URL might be invalid or inaccessible).
```

## Project Structure

```bash
meta-scraper/
├── main.py              # Main script
├── websites.json        # JSON file with a list of website URLs
├── output/              # Folder for generated metadata files
└── README.md            # Project documentation
```
