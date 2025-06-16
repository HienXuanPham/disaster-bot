# Use official Python image
FROM python:3.11-slim-bullseye

# Add system dependencies required for TLS/SSL
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  libssl-dev \
  ca-certificates \
  gcc \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose port
EXPOSE 8080

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]