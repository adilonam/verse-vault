FROM python:3.12-slim-bookworm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
# bible-sqlite.db is gitignored; it must exist in the build context at build time.
COPY bible-sqlite.db ./bible-sqlite.db

ENV BIBLE_VERSION_ID=4

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
