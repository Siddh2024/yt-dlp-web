FROM python:3.9-slim

# Install system dependencies (ffmpeg is required)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . .

# Expose port (Render sets PORT env variable)
EXPOSE 5000

# Run with Gunicorn
CMD ["python", "server.py"]
