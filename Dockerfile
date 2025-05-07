FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required by Playwright
RUN apt-get update && apt-get install -y wget gnupg curl && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Install Playwright and required browsers
RUN python -m playwright install

# Create a non-root user
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user

# Set environment variables
ENV PATH="/home/user/.local/bin:$PATH"
ENV CRAWL4AI_DB_PATH=/home/user/.crawl4ai

# Ensure the cache directory exists
RUN mkdir -p $CRAWL4AI_DB_PATH

# Install Playwright browsers for the non-root user
RUN python -m playwright install

# Run crawl4ai setup
RUN crawl4ai-setup

# Copy app code
COPY --chown=user . .

# Expose the Render port (default is to use $PORT)
EXPOSE 10000

# Use shell CMD so $PORT is respected
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers --forwarded-allow-ips '*'
