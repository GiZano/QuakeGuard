FROM python:3.11-slim

WORKDIR /app

# Install dependencies for PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set PYTHONPATH to include both /app and /app/src
ENV PYTHONPATH="/app:/app/src"

# Copy application code
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Command to start the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]