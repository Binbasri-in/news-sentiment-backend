import os
import json
import asyncio
from crawl4ai import AsyncWebCrawler
from unstructured.partition.html import partition_html
from unstructured.documents.elements import Title, NarrativeText
from urllib.parse import urlparse
from pathlib import Path


def sanitize_filename(url):
    sanitized = url.replace("https://", "").replace("http://", "").replace("/", "_").replace("?", "_")
    print(f"Sanitized filename: {sanitized}")
    return sanitized[:15]


def extract_from_markdown(markdown_content, url):
    # Treat markdown as HTML for Unstructured parsing
    elements = partition_html(text=markdown_content)

    title = ""
    content_lines = []

    for el in elements:
        if isinstance(el, Title) and not title:
            title = el.text
        elif isinstance(el, NarrativeText):
            content_lines.append(el.text)

    content = "\n".join(content_lines).strip()

    if not title:
        title = url.split("/")[-1]
        if not title:
            title = "No Title"
    if not content:
        content = "No Content"
    # Clean up content
    content = content.replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()
    if not content:
        content = "No Content"

    return {
        "url": url,
        "title": title.strip(),
        "content": content
    }


async def crawl_and_extract():
    # Output folders
    result_dir = Path("result")
    result_dir.mkdir(exist_ok=True)

    output_json_path = "extracted_articles.json"
    input_file = "list.txt"
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found.")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]


    # Validate URLs
    valid_urls = [url for url in urls if urlparse(url).scheme in ('http', 'https')]
    if not valid_urls:
        print("No valid URLs found in the input file.")
        return
    print(f"Found {len(valid_urls)} valid URLs.")
    async with AsyncWebCrawler(verbose=True) as crawler:
        results = await crawler.arun_many(
            urls=urls,
            bypass_cache=True,
            verbose=True,
        )

        extracted_articles = []

        for result in results:
            if result.success:
                print(f"Successfully crawled: {result.url}")

                filename = sanitize_filename(result.url) + ".md"
                filepath = result_dir / filename

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(result.markdown)

                article = extract_from_markdown(result.markdown, result.url)

                if article:
                    extracted_articles.append(article)
                    print(f"Extracted title: {article['title']}")
                else:
                    print(f"Failed to extract from {result.url}")
            else:
                print(f"Failed to crawl: {result.url}")
                print(f"Error: {result.error_message}")

        # Save extracted articles
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(extracted_articles, f, ensure_ascii=False, indent=4)

        print(f"\nExtraction completed. Articles saved to '{output_json_path}'")


if __name__ == "__main__":
    asyncio.run(crawl_and_extract())
