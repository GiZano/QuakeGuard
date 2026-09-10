# =============================================================================
# Stage 1: Build — install system deps and compile Python wheels
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary :all: --require-hashes \
    --prefix=/install -r requirements.txt

# =============================================================================
# Stage 2: Runtime — slim image with only compiled packages and app code
# =============================================================================
FROM python:3.11-slim AS runtime

RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 --no-create-home appuser

WORKDIR /app

# Copy pre-built Python packages from builder
COPY --from=builder /install /usr/local

# Set PYTHONPATH to include both /app and /app/src
ENV PYTHONPATH="/app:/app/src"

# Copy application code
COPY src/ ./src/

USER appuser

# Expose port
EXPOSE 8000

# Command to start the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]