# Small Python image
FROM python:3.12-slim

# Workdir
WORKDIR /app

# System deps (optional; add build-essential if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \    ca-certificates \ && rm -rf /var/lib/apt/lists/*

# Copy requirements separately for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose Flask port
EXPOSE 5000

# Use gunicorn in production
ENV PORT=5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
