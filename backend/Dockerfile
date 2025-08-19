# syntax=docker/dockerfile:1.7

# ===== Base builder (installs deps) =====
FROM python:3.11-slim AS builder

ENV POETRY_VERSION=1.8.3 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (use the existing pinned requirements file)
COPY requirement.txt ./requirement.txt

# Create a virtualenv to keep runtime lean
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -r requirement.txt

# ===== Runtime image =====
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000

WORKDIR /app

# Runtime deps for psycopg2
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy Alembic config and backend source
COPY alembic.ini ./alembic.ini
COPY app ./app

# Add a non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app
USER appuser

# Expose port (Cloud Run honors $PORT)
EXPOSE 8000

# Default command uses uvicorn (gunicorn not necessary on Cloud Run)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


