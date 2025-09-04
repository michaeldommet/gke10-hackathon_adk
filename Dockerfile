# Use the official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user first
RUN adduser --disabled-password --gecos "" appuser

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user for uv installation
USER appuser

# Install uv/uvx for the appuser
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy the application code
COPY --chown=appuser:appuser . .

# Set PATH for user local bin and uv
ENV PATH="/home/appuser/.cargo/bin:/home/appuser/.local/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8080

# Run the application
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]