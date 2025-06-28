FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a directory for local secret storage
RUN mkdir -p /app/data

# Make main.py executable
RUN chmod +x main.py

# Expose port for FastAPI
EXPOSE 8000

# Default command (can be overridden)
CMD ["python", "api.py"]
