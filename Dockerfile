FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY run.py .

ENV PYTHONPATH=/app/backend

EXPOSE 8001

CMD ["python", "run.py"]
