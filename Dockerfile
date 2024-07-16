# Build

FROM python:3.11-alpine AS builder
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    python3-dev \
    build-base \
    curl
RUN pip install --upgrade pip && pip install poetry==1.8.3
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache
WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR


# Run

FROM python:3.11-alpine
LABEL name="Teemo" \
      description="Hop, Two Three Four!" \
      url="https://github.com/ipromknight/teemo"

ENV PYTHONUNBUFFERED=1
RUN apk add --no-cache \
    curl \
    shadow \
    unzip \
    gcc \
    musl-dev \
    libffi-dev \
    python3-dev \
    libpq-dev

RUN pip install poetry==1.8.3

ENV FORCE_COLOR=1
ENV TERM=xterm-256color

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY teemo/ /app/teemo
COPY pyproject.toml poetry.lock VERSION entrypoint.sh /app/

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]