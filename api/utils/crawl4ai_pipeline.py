import logging
from sqlalchemy.orm import Session
from crawl4ai import AsyncWebCrawler
from unstructured.partition.html import partition_html
from unstructured.documents.elements import Title, NarrativeText
from tensorflow.nn import softmax as tf_softmax
from numpy import argmax
import requests

from api.models import Profile, Article
from api.ml_models import get_model
from api.utils.helpers import get_session_with_agent

logger = logging.getLogger(__name__)

class Crawl4AIPipeline:
    def __init__(self, db: Session, max_links_per_profile: int = 10):
        self.db = db
        self.max_links_per_profile = max_links_per_profile
        self.inverse_category_mapping = {v: k for k, v in {
            "Entertainment": 0,
            "Business": 1,
            "Politics": 2,
            "Judiciary": 3,
            "Crime": 4,
            "Culture": 5,
            "Sports": 6,
            "Science": 7,
            "International": 8,
            "Technology": 9
        }.items()}
        self.category_ministry_mapping = {
            "Entertainment": "Ministry of Information and Broadcasting",
            "Business": "Ministry of Finance",
            "Politics": "Ministry of Parliamentary Affairs",
            "Judiciary": "Ministry of Law and Justice",
            "Crime": "Ministry of Home Affairs",
            "Culture": "Ministry of Culture",
            "Sports": "Ministry of Youth Affairs and Sports",
            "Science": "Ministry of Science and Technology",
            "International": "Ministry of External Affairs",
            "Technology": "Ministry of Electronics and Information Technology"
        }
        self.session = get_session_with_agent()

    def predict_sentiment(self, text: str) -> dict:
        tokenizer = get_model("sentiment_tokenizer")
        model = get_model("sentiment_model")
        inputs = tokenizer(text, return_tensors="tf", truncation=True, max_length=512, padding=True)
        outputs = model(inputs)
        scores = tf_softmax(outputs.logits, axis=1)[0].numpy()
        labels = ["negative", "neutral", "positive"]
        max_score = argmax(scores)
        return {
            "sentiment": labels[max_score],
            "scores": {
                "negative": scores[0].item(),
                "neutral": scores[1].item(),
                "positive": scores[2].item()
            }
        }

    def predict_news_category(self, text: str) -> str:
        tokenizer = get_model("news_tokenizer")
        model = get_model("news_model")
        inputs = tokenizer(text, return_tensors="tf", truncation=True, padding=True, max_length=512)
        outputs = model(inputs)
        probs = tf_softmax(outputs.logits, axis=1)[0].numpy()
        predicted_index = argmax(probs)
        return self.inverse_category_mapping.get(predicted_index, f"label_{predicted_index}")

    async def run(self):
        profiles = self.db.query(Profile).all()
        if not profiles:
            logger.info("No profiles found to crawl.")
            return

        async with AsyncWebCrawler() as crawler:
            for profile in profiles:
                logger.info(f"Crawling profile: {profile.name} ({profile.base_url})")

                try:
                    urls = await extract_all_urls(profile.base_url, crawler)
                    if not urls:
                        logger.info(f"No URLs found for profile {profile.name}")
                        continue

                    logger.info(f"Found {len(urls)} URLs for profile {profile.name}")
                    urls = urls[:self.max_links_per_profile]

                    for link_obj in urls:
                        url = link_obj["href"]
                        if self.db.query(Article).filter_by(url=url).first():
                            logger.debug(f"Article already exists: {url}")
                            continue
                        if len(url) < 50:
                            logger.info(f"URL too short: {url}. Skipping.")
                            continue

                        result = extract_article_unstructured_html(url, self.session)
                        if not result:
                            logger.info(f"Failed to extract article from {url}. Skipping.")
                            continue

                        title = result.get("title")
                        content = result.get("content")
                        if not title or len(title.split()) < 5 or not content or len(content) < 1000:
                            logger.info(f"Incomplete or insufficient content from {url}. Skipping.")
                            continue

                        classification = self.predict_news_category(content)
                        sentiment = self.predict_sentiment(content)
                        logger.debug(f"Classified as {classification}, Sentiment: {sentiment}")

                        scores = sentiment.get("scores", {})
                        ministry = self.category_ministry_mapping.get(classification, "Unknown")

                        article = Article(
                            source_id=profile.id,
                            url=url,
                            title=title,
                            content=content,
                            classification=classification,
                            sentiment=sentiment["sentiment"],
                            ministry_to_report=ministry,
                            positive_sentiment=int(scores.get("positive", 0) * 100),
                            negative_sentiment=int(scores.get("negative", 0) * 100),
                            neutral_sentiment=int(scores.get("neutral", 0) * 100),
                        )
                        self.db.add(article)
                        self.db.commit()
                        self.db.refresh(article)
                        logger.info(f"Saved article: {article.title}")

                except Exception as e:
                    logger.error(f"Error processing profile {profile.name}: {e}")

# Helper functions reused from working class

async def extract_all_urls(url: str, crawler: AsyncWebCrawler):
    logger.info(f"Extracting URLs from {url}")
    result = await crawler.arun(url)
    urls = []
    urls.extend(result.links.get("external", []))
    urls.extend(result.links.get("internal", []))
    logger.info(f"Found {len(urls)} URLs in {url}")
    return urls

def extract_article_unstructured_html(url: str, session: requests.Session = None):
    session = session or get_session_with_agent()
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
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
