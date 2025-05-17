import logging
import requests
from unstructured.documents.elements import Title, NarrativeText
from unstructured.partition.html import partition_html
from numpy import argmax
from torch import no_grad
from torch.nn.functional import softmax
from tensorflow.nn import softmax as tf_softmax
import os

from api.ml_models import get_model

logger = logging.getLogger(__name__)

translation_url = "https://google-translate113.p.rapidapi.com/api/v1/translator/text"
detect_language_url = "https://google-translate113.p.rapidapi.com/api/v1/translator/detect-language"

headers = {
	"x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
	"x-rapidapi-host": "google-translate113.p.rapidapi.com",
	"Content-Type": "application/json"
}

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

    def detect_language(self, text: str):
        payload = {"text": text}
        response = requests.post(detect_language_url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("source_lang_code")
        else:
            logger.error(f"Language detection failed: {response.status_code} - {response.text}")
            return None
        
    def translate_to_english(self, text: str):
        logger.info(f"Translating text to English: {text}")
        payload = {
            "from": "auto",
            "to": "en",
            "text": text
        }
        response = requests.post(translation_url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("trans")
        else:
            logger.error(f"Translation failed: {response.status_code} - {response.text}")
            return None
        
    
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
        if len(title.split()) < 1:
            title = "No Title Extracted"
        if len(content) < 300:
            logger.warning(f"Content too short for analysis from URL: {url}")
            return None

        # detect language
        language_data = self.detect_language(content)
        if not language_data:
            logger.warning(f"Language detection failed for URL: {url}")
        
        # if anything other than English, translate to English
        if language_data != "en":
            translation_data = self.translate_to_english(content)
            if not translation_data:
                logger.warning(f"Translation failed for URL: {url}")
            else:
                content = translation_data
                logger.info(f"Translated content to English for URL: {url}")
                logger.debug(f"Translated content: {content}")
        else:
            logger.info(f"Content is already in English for URL: {url}")
            
        # predict sentiment and category
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
