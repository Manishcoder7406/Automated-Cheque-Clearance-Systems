FROM python:3.11-slim

WORKDIR /app

COPY bank_env /app/bank_env

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r /app/bank_env/requirements.txt

EXPOSE 7860

CMD ["streamlit", "run", "bank_env/server/app.py", "--server.port", "7860", "--server.address", "0.0.0.0"]
