FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends     curl build-essential ca-certificates     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first (better layer caching)
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy app code
COPY api ./api
COPY worker ./worker

EXPOSE 8000

# default command will be overridden by docker-compose
CMD ["bash", "-lc", "echo 'Specify a command (api or worker) in docker-compose.yml' && sleep infinity"]
