FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
COPY config.json .
COPY . .

ARG TOKEN
ENV TOKEN=${TOKEN}

ARG FOOTBALL_API_KEY
ENV FOOTBALL_API_KEY=${FOOTBALL_API_KEY}

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
