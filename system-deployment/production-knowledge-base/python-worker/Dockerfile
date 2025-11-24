FROM python:3.11-slim

WORKDIR /app

# Copy application files
COPY script.py .
COPY requirements.txt .

# Install Dependencies
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONUNBUFFERED=1

# Expose FastAPI port
EXPOSE 5000

# Run script
CMD ["python", "-u", "script.py"]
