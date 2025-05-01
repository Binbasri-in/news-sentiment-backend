import asyncio
import requests
import trafilatura
import psycopg2
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# --------------------- CONFIG ---------------------
DB_CONFIG = {
    'dbname': 'your_db',
    'user': 'your_user',
    'password': 'your_pass',
    'host': 'localhost',
    'port': 5432,
}


# --------------------- DATABASE ---------------------
class Database:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)

    def fetch_sources(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, url FROM news_sources;")
            return cur.fetchall()

    def save_article(self, source_id, url, title, content):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO articles (source_id, url, title, content)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING;
            """, (source_id, url, title, content))
            self.conn.commit()


# --------------------- CRAWLER ---------------------
class Crawler:
    def __init__(self, use_playwright=False):
        self.use_playwright = use_playwright

    async def get_page_links(self, url):
        if self.use_playwright:
            return await self._get_links_with_playwright(url)
        else:
            return self._get_links_with_requests(url)

    def _get_links_with_requests(self, url):
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        links = set(a['href'] for a in soup.find_all('a', href=True))
        return list(links)

    async def _get_links_with_playwright(self, url):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=30000)
            content = await page.content()
            await browser.close()
        soup = BeautifulSoup(content, 'html.parser')
        links = set(a['href'] for a in soup.find_all('a', href=True))
        return list(links)


# --------------------- EXTRACTOR ---------------------
class Extractor:
    def extract(self, url):
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None, None
        result = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if not result:
            return None, None
        soup = BeautifulSoup(downloaded, 'html.parser')
        title = soup.title.string if soup.title else 'No Title'
        return title.strip(), result.strip()


# --------------------- NLP PIPELINE ---------------------
class NLPPipeline:
    def process(self, title, content):
        # Replace this with your actual pipeline
        # e.g., summarization, keyword extraction, etc.
        return title, content  # Mock: pass-through


# --------------------- MAIN PIPELINE ---------------------
class NewsPipeline:
    def __init__(self):
        self.db = Database()
        self.crawler = Crawler(use_playwright=True)
        self.extractor = Extractor()
        self.nlp = NLPPipeline()

    async def run(self):
        sources = self.db.fetch_sources()

        for source_id, url in sources:
            print(f"Crawling source: {url}")
            try:
                links = await self.crawler.get_page_links(url)
            except Exception as e:
                print(f"Failed to crawl {url}: {e}")
                continue

            for link in links:
                if not link.startswith('http'):
                    continue
                print(f"Processing article: {link}")
                try:
                    title, content = self.extractor.extract(link)
                    if not content:
                        continue
                    title, content = self.nlp.process(title, content)
                    self.db.save_article(source_id, link, title, content)
                except Exception as e:
                    print(f"Failed to process article {link}: {e}")


# --------------------- ENTRY POINT ---------------------
if __name__ == "__main__":
    pipeline = NewsPipeline()
    asyncio.run(pipeline.run())
