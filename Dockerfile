FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY shared/ ./shared/
COPY services/ ./services/
COPY run.py .
COPY pytest.ini .

EXPOSE 8000 8001 8002 8003 8004 8005 8006 8007 8008 8009

CMD ["python", "run.py"]
