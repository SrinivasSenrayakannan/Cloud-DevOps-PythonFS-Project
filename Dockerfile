FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Run Gunicorn, point to app.py:app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--chdir", "/app", "app:app"]
