# Backend Dockerfile for BrandTruth AI API
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for playwright and general use
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    curl \
    wget \
    gnupg \
    # Playwright dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright browsers
RUN playwright install chromium

# Copy application code
COPY src/ ./src/
COPY api_server.py .
COPY jobs/ ./jobs/

# Create output directory
RUN mkdir -p output

# Expose port
EXPOSE 8000

# Run the API server
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
