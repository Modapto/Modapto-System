FROM python:3.11-slim

WORKDIR /app

# Copy application files
COPY script.py .
COPY requirements.txt .

# Install Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run script
CMD ["python", "-u", "script.py"]
