# Use Python 3.11 slim image
FROM python:3.11-slim

# Prevent Python from creating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (required by some Python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Cloud Run provides the PORT environment variable
ENV PORT=8080

# Expose the Cloud Run port
EXPOSE 8080

# Start Streamlit
CMD ["sh", "-c", "streamlit run ui/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true"]