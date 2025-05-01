import logging
from sqlalchemy.orm import Session
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter


from torch import no_grad
from torch.nn.functional import softmax
from tensorflow.nn import softmax as tf_softmax
from numpy import argmax

from api.ml_models import ml_models
from api.models import Profile, Article
from api.ml_models import get_model

    
# Configure logging
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

    def predict_sentiment(self, text: str) -> str:
        tokenizer = get_model("sentiment_tokenizer")
        model = get_model("sentiment_model")
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with no_grad():
            outputs = model(**inputs)
        scores = softmax(outputs.logits, dim=1)[0]
        labels = ["negative", "neutral", "positive"]
        return labels[scores.argmax().item()]

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

        browser_config = BrowserConfig(headless=True, verbose=True)
        markdown_generator = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.5, threshold_type="fixed")
        )
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            for profile in profiles:
                logger.info(f"Crawling profile: {profile.name} ({profile.base_url})")
                try:
                    result = await crawler.arun(profile.base_url, config=crawler_config)
                    if not result.success:
                        logger.warning(f"Failed to crawl {profile.base_url}")
                        continue

                    links = result.links["internal"] + result.links["external"]
                    links = links[:self.max_links_per_profile]
                    logger.info(f"Found {len(links)} links for profile {profile.name}")

                    for link_obj in links:
                        link = link_obj["href"]
                        if self.db.query(Article).filter_by(url=link).first():
                            logger.debug(f"Article already exists: {link}")
                            continue
                        if len(link) < 50:
                            logger.debug(f"Link too short: {link}")
                            continue

                        article_result = await crawler.arun(link, config=crawler_config)
                        if not article_result.success:
                            logger.warning(f"Failed to crawl article: {link}")
                            continue

                        raw_content = article_result.markdown.raw_markdown.strip().replace("\n", " ")
                        if not raw_content:
                            logger.warning(f"No content extracted for article: {link}")
                            continue

                        title = link.replace("_", " ").title()
                        content = raw_content

                        classification = self.predict_news_category(content)
                        sentiment = self.predict_sentiment(content)

                        article = Article(
                            source_id=profile.id,
                            url=link,
                            title=title,
                            content=content,
                            classification=classification,
                            sentiment=sentiment
                        )
                        self.db.add(article)
                        self.db.commit()
                        logger.info(f"Saved article: {title}")
                except Exception as e:
                    logger.error(f"Error processing profile {profile.name}: {e}")


  
# This class is for crawling a single profile                
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
    
    def predict_sentiment(self, text: str) -> str:
        tokenizer = get_model("sentiment_tokenizer")
        model = get_model("sentiment_model")
        
        # Truncate text to max_length supported by model
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        
        with no_grad():
            outputs = model(**inputs)
        
        scores = softmax(outputs.logits, dim=1)[0]
        labels = ["negative", "neutral", "positive"]
        return labels[scores.argmax().item()]

    def predict_news_category(self, text: str) -> str:
        tokenizer = get_model("news_tokenizer")
        model = get_model("news_model")
        
        # Truncate text for classification
        inputs = tokenizer(text, return_tensors="tf", truncation=True, padding=True, max_length=512)
        
        outputs = model(inputs)
        probs = tf_softmax(outputs.logits, axis=1)[0].numpy()
        predicted_index = argmax(probs)
        return self.inverse_category_mapping.get(predicted_index, f"label_{predicted_index}")

    async def run(self):
        if not self.profile:
            logger.info("No profile found to crawl.")
            return

        browser_config = BrowserConfig(headless=True, verbose=True)
        markdown_generator = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.5, threshold_type="fixed")
        )
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=markdown_generator
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            logger.info(f"Crawling profile: {self.profile.name} ({self.profile.base_url})")
            result = await crawler.arun(self.profile.base_url, config=crawler_config)
            if not result.success:
                logger.warning(f"Failed to crawl {self.profile.base_url}")
                return
            logger.debug(f"Result: {result.links}")
            links = result.links
            logger.info(f"Found {len(links)} links for profile {self.profile.name}")

            logger.debug(f"Links: {links}")
            links = links["internal"] + links["external"]
            
            for link_obj in links:
                link = link_obj['href']
                logger.debug(f"Processing: {link}")
                if self.db.query(Article).filter_by(url=link).first():
                    logger.debug(f"Article already exists: {link}")
                    continue
                if len(link) < 50:
                    logger.debug(f"Link too short: {link}")
                    continue
                
                article_result = await crawler.arun(
                    link, 
                    config=crawler_config,
                )
                logger.debug(f"Article result: {article_result}")
                if not article_result.success:
                    logger.warning(f"Failed to crawl article: {link}")
                    continue
                
                article_data = article_result.markdown.raw_markdown
                article_data = article_data.replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()
                if isinstance(article_data, str):
                    article_data = {
                        "title": link.replace("_", " ").title(),
                        "content": article_data
                    }
                
                if not article_data:
                    logger.warning(f"No data extracted for article: {link}")
                    continue
                
                title = article_data.get("title", "No Title")
                content = article_data.get("content", "").replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()
                
                if not content:
                    logger.warning(f"No content extracted for article: {link}")
                    continue

                classification = self.predict_news_category(content)
                sentiment = self.predict_sentiment(content)
                
                logger.debug(f"Classification: {classification}, Sentiment: {sentiment}")
                
                if not classification or not sentiment:
                    logger.warning(f"Failed to classify article: {link}")
                    classification = "other"
                    sentiment = "Neutral"
                
                article = Article(
                    source_id=self.profile.id,
                    url=link,
                    title=title,
                    content=content,
                    classification=classification,
                    sentiment=sentiment
                )
                self.db.add(article)
                self.db.commit()
                logger.info(f"Saved article: {title}")
            logger.info(f"Finished processing profile: {self.profile.name}")
