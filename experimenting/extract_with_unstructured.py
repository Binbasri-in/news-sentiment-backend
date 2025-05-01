import os
import json
import requests
from urllib.parse import urlparse
from unstructured.partition.html import partition_html
from unstructured.documents.elements import Title, NarrativeText

def validate_link(url):
    parsed = urlparse(url)
    return all([parsed.scheme in ('http', 'https'), parsed.netloc])

def extract_article(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None

    elements = partition_html(text=response.text)

    title = ""
    content_lines = []

    for el in elements:
        if isinstance(el, Title) and not title:
            title = el.text
        elif isinstance(el, NarrativeText):
            content_lines.append(el.text)

    content = "\n".join(content_lines).strip()

    return {
        "url": url,
        "title": title.strip(),
        "content": content
    }

def main():
    input_file = "list.txt"
    output_file = "extracted_articles.json"

    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found.")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    valid_urls = [url for url in urls if validate_link(url)]

    extracted_data = []

    for url in valid_urls:
        print(f"Processing: {url}")
        article = extract_article(url)
        if not article:
            print(f"Failed to extract article from {url}")
            continue
        if not article.get("title"):
            print(f"No title found for {url}. Skipping.")
            continue
        if not article.get("content"):
            print(f"No content found for {url}. Skipping.")
            continue
        
        if len(article["content"]) < 100:
            print(f"Content too short for {url}. Skipping.")
            continue
        
        if article:
            extracted_data.append(article)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=4)

    print(f"Extraction completed. Results saved to '{output_file}'.")

if __name__ == "__main__":
    main()
