from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
from api.database import SessionLocal
from api.utils.crawl4ai_pipeline import Crawl4AIPipeline

def start_scheduler():
    scheduler = BackgroundScheduler()

    def job():
        db = SessionLocal()
        try:
            print("Running scheduled news crawler...")
            asyncio.run(Crawl4AIPipeline(db).run())
        finally:
            db.close()

    scheduler.add_job(job, 'interval', hours=24)
    scheduler.start()
