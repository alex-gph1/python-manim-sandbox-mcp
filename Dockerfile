FROM python:slim AS base

FROM base AS builder

# Install all necessary system dependencies for pycairo, manimpango, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    pkg-config \
    python3-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgirepository1.0-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY uv.lock pyproject.toml /app/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-install-project --no-dev
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev

FROM base
# Runtime dependencies (lighter)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgirepository-1.0-1 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8765
CMD ["sandbox-server"]
