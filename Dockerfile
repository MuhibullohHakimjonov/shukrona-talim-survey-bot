# Use official Python 3.12 slim base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Copy entrypoint script
COPY entrypoint.sh .

# Convert line endings to Unix format and set executable permissions
RUN dos2unix entrypoint.sh && chmod +x entrypoint.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1


ENTRYPOINT ["./entrypoint.sh"]