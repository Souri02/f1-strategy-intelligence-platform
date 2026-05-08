FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.full.txt ./requirements.full.txt
RUN pip install --no-cache-dir -r requirements.full.txt

COPY backend/app ./app
COPY backend/run_*.py ./
COPY pipelines ./pipelines
COPY scripts ./scripts

ENV PYTHONPATH=/app

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
