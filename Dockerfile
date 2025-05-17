FROM python:3.11

WORKDIR /app

# Install Python dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and download the required browsers with dependencies
RUN python -m playwright install --with-deps

# Create and switch to a non-root user (required by Hugging Face Spaces)
RUN useradd -m -u 1000 user
RUN chown -R 1000:1000 /app
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Set environment variable for crawl4ai DB/cache path
ENV CRAWL4AI_DB_PATH=/home/user/.crawl4ai

# Ensure the cache directory exists for the non-root user
RUN mkdir -p $CRAWL4AI_DB_PATH

# Install Playwright browsers for the non-root user
RUN python -m playwright install

# Run crawl4ai setup as non-root
RUN crawl4ai-setup

# Copy the full codebase
COPY --chown=user . .
# Expose FastAPI port
EXPOSE 7860
# Launch FastAPI app using uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860", "--proxy-headers", "--forwarded-allow-ips", "*"]