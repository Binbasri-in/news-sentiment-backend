import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from collections import defaultdict


from api.database import get_db
from api.models import Profile, Article
from api.schemas import ProfileCreate, ProfileOut
from api.utils.unstructured_pipeline import Crawl4AIPipelineSingleProfile

# Configure logging
logger = logging.getLogger(__name__)


router = APIRouter()

@router.post("/", response_model=ProfileOut)
def create_profile(profile: ProfileCreate, db: Session = Depends(get_db)):
    logger.debug("Attempting to create profile with data: %s", profile.dict())
    try:
        existing = db.query(Profile).filter(Profile.name == profile.name).first()
        if existing:
            logger.debug("Profile with name '%s' already exists", profile.name)
            raise HTTPException(status_code=400, detail="Profile already exists")
        new_profile = Profile(**profile.dict())
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        logger.debug("Profile created successfully: %s", new_profile)
        return new_profile
    except Exception as e:
        logger.error("An error occurred while creating the profile: %s", str(e))
        raise HTTPException(status_code=500, detail="An error occurred while creating the profile")


@router.get("/", response_model=list[ProfileOut])
def get_profiles(db: Session = Depends(get_db)):
    logger.debug("Fetching all profiles")
    profiles = db.query(Profile).all()
    logger.debug("Fetched profiles: %s", profiles)
    return profiles


@router.get("/{profile_name}", response_model=ProfileOut)
def get_profile(profile_name: str, db: Session = Depends(get_db)):
    logger.debug("Fetching profile with name: %s", profile_name)
    profile = db.query(Profile).filter(Profile.name == profile_name).first()
    if not profile:
        logger.debug("Profile with name '%s' not found", profile_name)
        raise HTTPException(status_code=404, detail="Profile not found")
    logger.debug("Fetched profile: %s", profile)
    return profile


@router.put("/{profile_name}", response_model=ProfileOut)
def update_profile(profile_name: str, profile_update: ProfileCreate, db: Session = Depends(get_db)):
    logger.debug("Updating profile with name: %s using data: %s", profile_name, profile_update.dict())
    profile = db.query(Profile).filter(Profile.name == profile_name).first()
    if not profile:
        logger.debug("Profile with name '%s' not found", profile_name)
        raise HTTPException(status_code=404, detail="Profile not found")
    for key, value in profile_update.dict().items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    logger.debug("Profile updated successfully: %s", profile)
    return profile


@router.delete("/{profile_name}")
def delete_profile(profile_name: str, db: Session = Depends(get_db)):
    logger.debug("Deleting profile with name: %s", profile_name)
    profile = db.query(Profile).filter(Profile.name == profile_name).first()
    if not profile:
        logger.debug("Profile with name '%s' not found", profile_name)
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(profile)
    db.commit()
    logger.debug("Profile '%s' deleted successfully", profile_name)
    return {"message": f"Profile '{profile_name}' deleted successfully."}


################################
# Extra functionalities
################################

# manual crawling trigger
@router.post("/{profile_name}/crawl")
async def trigger_crawl(profile_name: str, request: Request, db: Session = Depends(get_db)):
    logger.debug("Triggering crawl for profile with name: %s", profile_name)
    profile = db.query(Profile).filter(Profile.name == profile_name).first()
    if not profile:
        logger.debug("Profile with name '%s' not found", profile_name)
        return {"message": f"Profile '{profile_name}' not found."}
    
    # check if the profile is already crawled
    if profile.crawling_state == "crawled":
        logger.debug("Profile '%s' is already crawled", profile_name)
        return {"message": f"Profile '{profile_name}' is already crawled."}
    
    # Here you would call the function to start the crawling process
    try:
        pipeline = Crawl4AIPipelineSingleProfile(db=db, profile=profile)
        await pipeline.run(crawler=request.app.state.crawler)
        
    except Exception as e:
        logger.error("An error occurred while triggering the crawl: %s", str(e))
        return {"message": f"Crawl triggered for profile '{profile_name}'."}
    
    logger.debug("Crawl triggered successfully for profile: %s", profile)
    return {"message": f"Crawl triggered for profile '{profile_name}'."}


# the profile analytic generation
@router.get("/{profile_id}/analytics")
def get_profile_analytics(profile_id: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.name == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    articles = db.query(Article).filter(Article.source_id == profile.id).all()

    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    section_sentiment = defaultdict(lambda: {"positive": 0, "neutral": 0, "negative": 0})
    top_positive = []
    top_negative = []

    for article in articles:
        sentiment_counts[article.sentiment.lower()] += 1
        section_sentiment[article.classification][article.sentiment.lower()] += 1

        score = (article.positive_sentiment or 0) - (article.negative_sentiment or 0)
        if score > 0:
            top_positive.append((score, article))
        elif score < 0:
            top_negative.append((score, article))

    top_positive = sorted(top_positive, key=lambda x: -x[0])[:10]
    top_negative = sorted(top_negative, key=lambda x: x[0])[:10]

    return {
        "sentiment_counts": sentiment_counts,
        "section_sentiment": section_sentiment,
        "top_positive_articles": [
            {"title": a.title, "section": a.classification, "score": s}
            for s, a in top_positive
        ],
        "top_negative_articles": [
            {"title": a.title, "section": a.classification, "score": s}
            for s, a in top_negative
        ]
    }
