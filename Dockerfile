FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Native dependencies for audio and Whisper/ffmpeg support.
# Apply security upgrades during build to reduce known CVEs from base layers.
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libportaudio2 \
    portaudio19-dev \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Default to a non-interactive smoke test in containers.
CMD ["python", "test_cartesia_simple.py"]
