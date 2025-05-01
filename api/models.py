from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from api.database import Base
from datetime import datetime


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)  
    base_url = Column(String, nullable=False)                       
    language = Column(String, nullable=False)                       
    crawling_strategy = Column(String, nullable=False)
    crawling_state = Column(String, nullable=False, default="not_started")
    last_crawled = Column(DateTime, nullable=True)                 
    is_active = Column(Boolean, default=True)

    articles = relationship("Article", back_populates="source", cascade="all, delete")


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    author = Column(String, nullable=True)  # New: author name if available
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow)

    classification = Column(String, nullable=False)
    sentiment = Column(String, nullable=False)

    thumbnail_url = Column(String, nullable=True)  # New: image thumbnail for frontend preview
    tags = Column(String, nullable=True)           # New: comma-separated tags like "politics,world"
    
    is_featured = Column(Boolean, default=False)   # New: highlight special articles
    is_reported = Column(Boolean, default=False)   # New: user can report article if it's misinformation
    reported_reason = Column(Text, nullable=True)  # Optional reason provided by the user when reported

    source = relationship("Profile", back_populates="articles")
