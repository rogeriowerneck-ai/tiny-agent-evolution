FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir pytest

COPY app.py .
COPY tools.py .
COPY eval.py .
COPY test_agent.py .

CMD ["python", "app.py"]
