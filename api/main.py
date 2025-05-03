from pathlib import Path
from contextlib import asynccontextmanager
from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                          TFAutoModelForSequenceClassification)
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

from api.database import Base, engine
from api.routers import profiles, trigger, articles, dashboard
from api.scheduler import start_scheduler
from api.config import setup_logging
from api.ml_models import load_models

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    start_scheduler()
    # Load ML models at startup
    load_models()
    print("ML models loaded.")
    browser_config = BrowserConfig(headless=True, verbose=True)
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()
    # Store crawler in app state
    app.state.crawler = crawler
    yield
    # Cleanup code can be added here if needed
    await crawler.close()
    print("Shutting down...")
    
app = FastAPI(lifespan=lifespan)

Base.metadata.create_all(bind=engine)
app.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])   
app.include_router(trigger.router, prefix="/auto", tags=["auto"]) 
app.include_router(articles.router, prefix="/articles", tags=["Articles"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=JSONResponse)
def dashboard():
    return {"message": "Welcome to the Dashboard"}

# --- Global 404 handler ---
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(content={"error": "Resource not found"}, status_code=404)
    else:
        # For other HTTP errors (403, 500, etc.) you can customize further if you want
        return JSONResponse(content={"error": f"Error {exc.status_code}: {exc.detail}"}, status_code=exc.status_code)
