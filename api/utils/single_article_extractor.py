import logging
import requests
from unstructured.documents.elements import Title, NarrativeText
from unstructured.partition.html import partition_html
from numpy import argmax
from torch import no_grad
from torch.nn.functional import softmax
from tensorflow.nn import softmax as tf_softmax

from api.ml_models import get_model

logger = logging.getLogger(__name__)

class SingleArticleExtractor:
    def __init__(self):
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

    def extract_html_content(self, url: str, session: requests.Session = None):
        from api.utils.helpers import get_session_with_agent  # if needed
        session = session or get_session_with_agent()

        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
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
            "content": content.strip()
        }

    def predict_sentiment(self, text: str):
        tokenizer = get_model("sentiment_tokenizer")
        model = get_model("sentiment_model")
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

        with no_grad():
            outputs = model(**inputs)
        scores = softmax(outputs.logits, dim=1)[0]

        labels = ["negative", "neutral", "positive"]
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

    def predict_category(self, text: str):
        tokenizer = get_model("news_tokenizer")
        model = get_model("news_model")
        inputs = tokenizer(text, return_tensors="tf", truncation=True, padding=True, max_length=512)
        outputs = model(inputs)
        probs = tf_softmax(outputs.logits, axis=1)[0].numpy()
        predicted_index = argmax(probs)
        return self.inverse_category_mapping.get(predicted_index, f"label_{predicted_index}")

    def process(self, url: str):
        logger.info(f"Processing article from URL: {url}")
        result = self.extract_html_content(url)
        if not result:
            return None

        title = result.get("title")
        content = result.get("content")

        if not title or not content:
            logger.warning(f"Missing title or content for URL: {url}")
            return None

        if len(content) < 300:
            logger.warning(f"Content too short for analysis from URL: {url}")
            return None

        sentiment_data = self.predict_sentiment(content)
        classification = self.predict_category(content)
        scores = sentiment_data["scores"]
        ministry = self.category_ministry_mapping.get(classification, "Unknown")

        return {
            "url": url,
            "title": title,
            "content": content,
            "classification": classification,
            "sentiment": sentiment_data["sentiment"],
            "ministry_to_report": ministry,
            "positive_sentiment": int(scores["positive"] * 100),
            "negative_sentiment": int(scores["negative"] * 100),
            "neutral_sentiment": int(scores["neutral"] * 100),
        }
