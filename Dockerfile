FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY audit-tools/package.json audit-tools/package.json
RUN npm install --prefix audit-tools --omit=dev --no-audit --no-fund
RUN python -m playwright install --with-deps chromium
COPY mend ./mend
RUN mkdir -p /data /app/artifacts
RUN useradd -m -u 10001 mend && chown -R mend:mend /data /app/artifacts /app
USER mend
ENV MEND_DB_PATH=/data/mend.sqlite3 MEND_ARTIFACT_DIR=/app/artifacts
EXPOSE 8000
CMD ["uvicorn", "mend.api:app", "--host", "0.0.0.0", "--port", "8000"]
