# AI-Powered News Sentiment Analysis & Ministry Reporting System

## 📖 Overview

A comprehensive news monitoring and analysis platform that automatically crawls news articles, performs advanced sentiment analysis, classifies content by categories, and intelligently routes reports to relevant government ministries. The system leverages state-of-the-art AI models to process multilingual news content and provides real-time insights for content monitoring and governance.

## 🚀 Key Features

### 🤖 AI-Powered Analysis
- **Sentiment Analysis**: RoBERTa-based model for accurate emotion detection (Positive, Negative, Neutral)
- **News Classification**: DistilBERT model categorizing articles into 10+ categories
- **Multi-language Support**: Automatic language detection and translation to English
- **Content Extraction**: Advanced HTML parsing for clean article extraction

### 🔄 Automated Processing
- **Web Crawling**: Intelligent crawling using Crawl4AI and Playwright
- **Background Tasks**: Scheduled crawling and processing with APScheduler
- **Real-time Processing**: Instant analysis for single articles via API
- **Database Management**: SQLAlchemy ORM with PostgreSQL support

### 📊 Analytics & Reporting
- **Sentiment Trends**: Track emotional patterns across news sources
- **Category Analytics**: Distribution analysis by news categories
- **Ministry Routing**: Intelligent mapping to relevant government departments
- **Dashboard**: Comprehensive web interface for data visualization

### 📧 Communication System
- **Email Automation**: Brevo API integration for ministry notifications
- **Custom Templates**: Tailored email content for different ministries
- **Reporting Workflow**: Streamlined process for content flagging and reporting

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Sources   │────│   Crawl4AI       │────│   Content       │
│                 │    │   + Playwright    │    │   Extraction    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │────│   ML Models      │────│   Analysis      │
│   Backend       │    │   (Transformers)  │    │   Pipeline      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                                               │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PostgreSQL    │────│   SQLAlchemy     │────│   Data Storage  │
│   Database      │    │   ORM            │    │   & Management  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **FastAPI**: High-performance async web framework
- **SQLAlchemy**: Python SQL toolkit and ORM
- **PostgreSQL**: Robust relational database
- **Pydantic**: Data validation using Python type annotations

### AI/ML
- **Transformers**: Hugging Face transformers library
- **TensorFlow**: Deep learning framework
- **RoBERTa**: Sentiment analysis model
- **DistilBERT**: News classification model

### Web Scraping
- **Crawl4AI**: Advanced web crawling framework
- **Playwright**: Browser automation
- **Unstructured**: Document parsing and processing
- **BeautifulSoup**: HTML/XML parsing

### Additional Services
- **APScheduler**: Background task scheduling
- **Brevo API**: Email service integration
- **RapidAPI**: Translation services
- **Docker**: Containerization

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- PostgreSQL database
- API Keys:
  - Hugging Face Token
  - RapidAPI Key
  - Brevo API Key

## ⚡ Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd news-sentiment-analysis
```

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install --with-deps
```

### 3. Environment Variables
Create a `.env` file:
```env
DATABASE_URL=postgresql://username:password@localhost/dbname
HF_TOKEN=your_huggingface_token
RAPIDAPI_KEY=your_rapidapi_key
BREVO_API_KEY=your_brevo_api_key
FROM_EMAIL=your_email@domain.com
FROM_NAME=Your App Name
```

### 4. Database Setup
```bash
# Run Alembic migrations (if available)
alembic upgrade head

# Or let SQLAlchemy create tables automatically
python -c "from api.database import engine; from api.models import Base; Base.metadata.create_all(bind=engine)"
```

### 5. Run the Application
```bash
# Development server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn api.main:app --host 0.0.0.0 --port 10000
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker
docker build -t news-analyzer .
docker run -p 10000:10000 news-analyzer

# Or use Docker Compose (if docker-compose.yml exists)
docker-compose up -d
```

## 📚 API Documentation

Once running, access the interactive API documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`


## 📊 Monitoring & Analytics

The system provides comprehensive analytics including:
- Sentiment distribution across sources
- Category-wise article breakdown
- Top positive/negative articles
- Ministry-wise routing statistics
- Real-time processing metrics

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
