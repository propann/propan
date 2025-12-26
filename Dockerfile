FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY propan /app/propan

RUN pip install --no-cache-dir .

EXPOSE 9000

CMD ["python", "-m", "propan", "run", "hal-brain"]
