FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better caching
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy source code
COPY src/ src/
COPY data/ data/

# Environment variables
ARG TOKEN
ENV TOKEN=${TOKEN}

ARG FOOTBALL_API_KEY
ENV FOOTBALL_API_KEY=${FOOTBALL_API_KEY}

CMD ["telegram-bot"]
