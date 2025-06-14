import logging
from sqlalchemy.orm import Session
import asyncio
from urllib.parse import urlparse
from unstructured.partition.md import partition_md
from unstructured.documents.elements import Title, NarrativeText
from fastapi import Request
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
import requests
from unstructured.partition.html import partition_html


from tensorflow.nn import softmax as tf_softmax
from numpy import argmax

from api.ml_models import ml_models
from api.models import Profile, Article
from api.ml_models import get_model

    
# Configure logging
logger = logging.getLogger(__name__)

class Crawl4AIPipelineSingleProfile:
    def __init__(self, db: Session, profile: Profile, max_links_per_profile: int = 10):
        self.db = db
        self.profile = profile
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

    def predict_sentiment(self, text: str) -> str:
        tokenizer = get_model("sentiment_tokenizer")
        model = get_model("sentiment_model")
        inputs = tokenizer(text, return_tensors="tf", truncation=True, max_length=512, padding=True)
        outputs = model(inputs)
        scores = tf_softmax(outputs.logits, axis=1)[0].numpy()
        labels = ["negative", "neutral", "positive"]
        # return an object with the max score and the corresponding label, and all the scors too
        max_score = argmax(scores)
        sentiment = labels[max_score]
        return {
            "sentiment": sentiment,
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

    async def run(self, crawler: AsyncWebCrawler):
        logger.info(f"Starting crawl for profile: {self.profile.name}")
        if not self.profile:
            logger.info("No profile found to crawl.")
            return

        urls = await extract_all_urls(self.profile.base_url, crawler=crawler)

        if not urls:
            logger.info("No URLs found to crawl.")
            return

        logger.info(f"Found {len(urls)} URLs to crawl.")
        for link_obj in urls:
            url = link_obj["href"]
            if self.db.query(Article).filter_by(url=url).first():
                    logger.debug(f"Article already exists: {url}")
                    continue
            if len(url) < 50:
                logger.info(f"URL too short: {url}. Skipping.")
                continue

            result = extract_article_unstructured_html(url)
            if not result:
                logger.info(f"Failed to extract article from {url}. Skipping.")
                continue

            title = result.get("title")
            content = result.get("content")
            if not title:
                logger.info(f"Title or content missing for {url}. Skipping.")
                continue
            
            if not content:
                logger.info(f"No content extracted from {url}. Skipping.")
                continue
            
            if len(title.split()) < 5:
                logger.info(f"Title too short for {url}. Skipping.")
                continue
        
            if len(content) < 1000:
                logger.info(f"Content too short for {url}. Skipping.")
                continue
            
            logger.debug(f"Classifying and sentiment analysis for URL: {url}")
            classification = self.predict_news_category(content)
            sentiment = self.predict_sentiment(content)
            logger.error(f"Classification: {classification}, Sentiment: {sentiment}")
            if not classification or not sentiment:
                classification = "Unknown"
                sentiment = "Unknown"
                
            scores = sentiment.get("scores", {})
            logger.debug(f"Classification: {classification}, Sentiment: {sentiment}")
            ministry = self.category_ministry_mapping.get(classification, "Unknown")
            article = Article(
                source_id=self.profile.id,
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
            logger.info(f"Article saved: {article.title} from {article.url}")

        logger.info(f"Finished crawling for profile: {self.profile.name}")
       
        
def parse_article(markdown_content: str):
    """
    Parse the article content and extract relevant information.
    """
    elements = partition_md(text=markdown_content)
    
    # Initialize variables to store title and content
    title = ""
    content_lines = []
    
    # Iterate through the elements to find the title and content
    for el in elements:
        if isinstance(el, Title) and not title:
            title = el.text
        elif isinstance(el, NarrativeText):
            content_lines.append(el.text)
            
    # Combine the content lines into a single string
    content = "\n".join(content_lines).strip()

    return title.strip(), content
    
async def extract_article(url: str, crawler: AsyncWebCrawler):
    """
    Extract article content from a given URL.
    """
    logger.info(f"Extracting article from {url}")
    result = await crawler.arun(url)
    if not result.success:
        logger.error(f"Failed to crawl {url}: {result.error}")
        return None
    
    markdown_content = result.markdown.raw_markdown
    
    if not markdown_content:
        logger.error(f"No content extracted from {url}")
        return None
    return markdown_content
        
        
        
async def extract_all_urls(url: str, crawler: AsyncWebCrawler):
    """
    Extract all URLs from a given webpage.
    """
    logger.info(f"Extracting URLs from {url}")
    result = await crawler.arun(url)
    urls = []
    urls.extend(result.links["external"])
    urls.extend(result.links["internal"])
    
    logger.info(f"Found {len(urls)} URLs in {url}")
    return urls


def extract_article_unstructured_html(url: str):
    """
    Extract article content from a given URL using unstructured library.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.HTTPError as e:
        print(f"Failed to fetch {url}: {e}")
        return None
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