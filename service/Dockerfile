FROM python:3.10-slim

WORKDIR /app

# mediapipe / opencv 実行時の依存（Cloud Runでの落ちを減らす）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "2", "--timeout", "0", "main:app"]
