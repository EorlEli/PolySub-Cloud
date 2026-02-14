# Use Python 3.10 Slim image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install system dependencies (FFmpeg is required for burning subtitles)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Default command: Run the local server (can be overridden by Cloud Run)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
