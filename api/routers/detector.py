import logging
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from urllib.parse import urlparse

from api.database import get_db
from api.utils.single_article_extractor import SingleArticleExtractor

# Configure logging
logger = logging.getLogger(__name__)


router = APIRouter()


@router.post("/", response_class=JSONResponse)
def detect_sentiment(data: dict, ):
    # get the URL from the request body
    logger.info("Received data: %s", data)
    if not isinstance(data, dict):
        return JSONResponse(content={"error": "Invalid data format"}, status_code=400)
    if "url" not in data:
        return JSONResponse(content={"error": "URL is required"}, status_code=400)
    if not data.get("url"):
        return JSONResponse(content={"error": "URL is required"}, status_code=400)
    if not isinstance(data.get("url"), str):
        return JSONResponse(content={"error": "URL must be a string"}, status_code=400)
    
    url = data.get("url")
    print("URL:", url)
    # confirm the URL is valid
    if not urlparse(url).scheme:
        return JSONResponse(content={"error": "Invalid URL"}, status_code=400)
    
    # send the url to the business logic
    extractor = SingleArticleExtractor()
    article = extractor.process(url)
    if not article:
        return JSONResponse(content={"error": "Failed to process URL"}, status_code=500)
    return JSONResponse(content=article, status_code=200)
