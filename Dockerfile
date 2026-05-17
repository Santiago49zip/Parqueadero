FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend
COPY frontend ./frontend
COPY BD ./BD
COPY README.md ./README.md

EXPOSE 5000
CMD ["python", "-m", "backend.app"]
