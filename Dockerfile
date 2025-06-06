FROM python:3.11-slim

# Set environment variables for better Python behavior in containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Europe/Istanbul

# Install FFmpeg and dependencies in a single layer to save space
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf ~/.cache/pip /root/.cache

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x start.py

# Set environment variable to explicitly tell the bot where ffmpeg is
ENV FFMPEG_PATH=/usr/bin/ffmpeg

# Use our startup script instead of directly running main.py
CMD ["python", "start.py"]