# Multi-stage build using uv for faster dependency resolution
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation and copy mode for better performance
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Copy the rest of the application
COPY . .

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Final runtime stage
FROM python:3.12-slim-bookworm

WORKDIR /app

# Install system dependencies required for Manim and other features
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libcairo2-dev \
    libpango1.0-dev \
    pkg-config \
    python3-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Make sure we use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash sandbox && \
    chown -R sandbox:sandbox /app

USER sandbox

# Expose port for HTTP server mode
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sandbox; print('OK')" || exit 1

# Default command (can be overridden)
CMD ["sandbox-server"]
