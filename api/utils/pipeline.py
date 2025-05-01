import asyncio
import logging
import trafilatura
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from sqlalchemy.orm import Session
from api.models import Article, Profile
import random

# Configure logging
logger = logging.getLogger(__name__)

class Crawler:
    async def get_links(self, url: str):
        logger.debug(f"Starting to crawl links from: {url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(url, timeout=30000)
                html = await page.content()
                logger.debug(f"Successfully fetched page content for: {url}")
            except Exception as e:
                logger.error(f"Error fetching page content for {url}: {e}")
                await browser.close()
                return []
            await browser.close()
        soup = BeautifulSoup(html, "html.parser")
        links = list(set(a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith("http")))
        logger.debug(f"Found {len(links)} links on {url}")
        return links

class Extractor:
    def extract(self, url: str):
        logger.debug(f"Starting to extract content from: {url}")
        html = trafilatura.fetch_url(url)
        if not html:
            logger.warning(f"Failed to fetch HTML for: {url}")
            return None, None
        text = trafilatura.extract(html)
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string.strip() if soup.title else "No Title"
        logger.debug(f"Extracted title: {title} from {url}")
        return title, text.strip() if text else None

class NLPPipeline:
    def process(self, title, content):
        logger.debug("Processing content with NLP pipeline")

        # Placeholder: insert real NLP logic here
        classification = random.choice(["Politics", "Sports", "Technology", "Health"])
        sentiment = random.choice(["Positive", "Negative", "Neutral"])

        return {
            "title": title,
            "content": content,
            "classification": classification,
            "sentiment": sentiment
        }
class NewsPipeline:
    def __init__(self, db: Session):
        self.db = db
        self.crawler = Crawler()
        self.extractor = Extractor()
        self.nlp = NLPPipeline()

    async def run(self):
        logger.info("Starting NewsPipeline run")
        sources = self.db.query(Profile).all()
        logger.debug(f"Found {len(sources)} sources to process")
        for source in sources:
            logger.info(f"Processing source: {source.base_url}")
            try:
                links = await self.crawler.get_links(source.base_url)
                logger.debug(f"Found {len(links)} links for source: {source.base_url}")
                for link in links:
                    if self.db.query(Article).filter_by(url=link).first():
                        logger.debug(f"Skipping already processed link: {link}")
                        continue
                    title, content = self.extractor.extract(link)
                    if title and content:
                        nlp_results = self.nlp.process(title, content)
                        article = Article(
                            source_id=source.id,
                            url=link,
                            title=nlp_results["title"],
                            content=nlp_results["content"],
                            classification=nlp_results["classification"],
                            sentiment=nlp_results["sentiment"],
                        )
                        self.db.add(article)
                        self.db.commit()
                        logger.info(f"Added new article: {title} from {link}")
                    else:
                        logger.warning(f"Failed to extract content for link: {link}")
            except Exception as e:
                logger.error(f"Error processing {source.base_url}: {e}")


# single website crawling
async def crawl_single_website(url: str):
    logger.info(f"Starting to crawl single website: {url}")
    crawler = Crawler()
    extractor = Extractor()
    nlp = NLPPipeline()

    links = await crawler.get_links(url)
    logger.debug(f"Found {len(links)} links for single website: {url}")

    for link in links:
        title, content = extractor.extract(link)
        if title and content:
            nlp_results = nlp.process(title, content)
            logger.info(f"Processed article: {nlp_results['title']} from {link}")
        else:
            logger.warning(f"Failed to extract content for link: {link}")
    
    if links > 0:
        logger.info(f"Finished crawling single website: {url}")
    else:
        logger.warning(f"No valid links found on {url}")
