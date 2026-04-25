FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY pyproject.toml README.md ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY libs ./libs
COPY services/auth-service ./services/auth-service

RUN pip install --no-cache-dir -e . \
    && mkdir -p /tmp/legal_uploads

WORKDIR /app/services/auth-service

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
