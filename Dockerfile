FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local

WORKDIR /app

# System deps for libpq + C extensions spaCy may pull
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# --- builder ---
FROM base AS builder
COPY pyproject.toml uv.lock ./
COPY app ./app
RUN uv sync --frozen --no-dev

# Optional: small spaCy model. Comment out if you want to keep image lean.
RUN python -m spacy download en_core_web_sm || true

# --- final ---
FROM base AS final
COPY --from=builder /usr/local /usr/local
COPY app ./app
COPY migrations ./migrations

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "python -m migrations.run && uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
