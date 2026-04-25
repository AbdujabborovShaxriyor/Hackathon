FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY pyproject.toml README.md ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY libs ./libs
COPY services/rag-service ./services/rag-service

RUN pip install --no-cache-dir -e .

WORKDIR /app/services/rag-service

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
