FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir groq requests edge-tts rich flask

COPY hal_brain.py /app/hal_brain.py

EXPOSE 9000

CMD ["python", "/app/hal_brain.py"]
