FROM python:3.12-slim

WORKDIR /app

COPY analyzer/requirements.txt ./analyzer/requirements.txt
RUN pip install --no-cache-dir -r analyzer/requirements.txt

COPY analyzer/ ./analyzer/

CMD ["python", "-m", "analyzer.main"]
