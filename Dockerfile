FROM python:3.11-slim

WORKDIR /app

# Security Compliance: Avoid running as root in production containers
RUN useradd -m appuser && chown -R appuser /app

# Cache dependencies layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source logic
COPY app.py .

USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "2"]
