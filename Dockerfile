FROM python:3.12-slim

WORKDIR /app

# Copy source code and install
COPY pyproject.toml .
COPY src/ src/
COPY data/ data/
RUN pip install --no-cache-dir .

# Environment variables
ARG TOKEN
ENV TOKEN=${TOKEN}

ARG FOOTBALL_API_KEY
ENV FOOTBALL_API_KEY=${FOOTBALL_API_KEY}

CMD ["telegram-bot"]
