FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/gps-ingest/pyproject.toml ./
COPY services/gps-ingest/README.md ./
RUN pip install --upgrade pip \
    && pip install .

COPY services/gps-ingest/gps_ingest ./gps_ingest

ENTRYPOINT ["python", "-m", "gps_ingest"]
