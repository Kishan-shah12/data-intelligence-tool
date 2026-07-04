FROM python:3.10-slim

WORKDIR /app

# Install standard dependencies for data generation/processing
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install backend API dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY . .

WORKDIR /app/backend

# Standard deployment for Cloud Run CPU
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
