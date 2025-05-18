from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
import os
import logging

ml_models = {}
HF_TOKEN = os.getenv("HF_TOKEN")

def load_models():
    global ml_models

    sentiment_model_path = "binbasri1/roberta-twitter-sentiment-tf"
    news_model_path = "binbasri1/distilbert-news-classifier-custom"

    try:
        print(f"Loading sentiment model from: {sentiment_model_path}")
        ml_models["sentiment_model"] = TFAutoModelForSequenceClassification.from_pretrained(
            sentiment_model_path, token=HF_TOKEN
        )
        ml_models["sentiment_tokenizer"] = AutoTokenizer.from_pretrained(
            sentiment_model_path, token=HF_TOKEN
        )
    except Exception as e:
        logging.error(f"Failed to load sentiment model: {e}")

    try:
        print(f"Loading news model from: {news_model_path}")
        ml_models["news_model"] = TFAutoModelForSequenceClassification.from_pretrained(
            news_model_path, token=HF_TOKEN
        )
        ml_models["news_tokenizer"] = AutoTokenizer.from_pretrained(
            news_model_path, token=HF_TOKEN
        )
    except Exception as e:
        logging.error(f"Failed to load news model: {e}")

def get_model(name: str):
    return ml_models.get(name)
