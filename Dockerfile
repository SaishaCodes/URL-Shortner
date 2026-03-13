FROM python:3.11-slim
 
WORKDIR /app
 
# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=120 -r requirements.txt
 
# Copy app source
COPY app/ ./app/
COPY frontend/ ./frontend/
 
# Expose FastAPI port
EXPOSE 8000
 
# Run with uvicorn; init_db creates tables on startup
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]