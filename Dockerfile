# Alternative build using standard Python image with uv installed
FROM python:3.13-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libcairo2-dev \
    libpango1.0-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Set uv environment variables
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv venv /app/.venv && \
    uv pip install --no-deps -r pyproject.toml

# Copy application code
COPY . .

# Install the application
RUN uv pip install -e .

# Final runtime stage
FROM python:3.13-slim-bookworm

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app /app

# Set environment to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Create non-root user
RUN useradd --create-home --shell /bin/bash sandbox && \
    chown -R sandbox:sandbox /app && \
    mkdir -p /sandbox_area && chown sandbox:sandbox /sandbox_area

USER sandbox

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sandbox; print('OK')" || exit 1

CMD ["sandbox-server"]
