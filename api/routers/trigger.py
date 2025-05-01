from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.database import get_db
from api.utils.crawl4ai_pipeline import Crawl4AIPipeline
import asyncio

router = APIRouter()

@router.post("/run-crawler")
def run_crawler_manually(db: Session = Depends(get_db)):
    asyncio.run(Crawl4AIPipeline(db).run())
    return {"message": "News crawler executed manually"}
