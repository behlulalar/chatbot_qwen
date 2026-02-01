# Backend Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    wget \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p data/raw_pdfs data/processed_json data/archive data/chroma_db logs

# Set environment
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "run_server.py"]
