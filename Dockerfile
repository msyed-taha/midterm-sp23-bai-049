# Stage 1: Python dependencies. Cached between builds while requirements.txt is unchanged.
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: CI environment in which Jenkins retrains the model and runs the tests.
FROM base AS ci
RUN pip install --no-cache-dir pytest httpx

# Stage 3: the deployed FastAPI service, packaged with the freshly trained model.
FROM base AS runtime
RUN useradd --create-home appuser
COPY app.py .
COPY artifacts/ ./artifacts/
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
