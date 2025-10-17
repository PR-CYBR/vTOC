FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY adsb_proxy ./adsb_proxy
COPY scripts ./scripts
COPY templates ./templates
COPY README.md ./README.md

EXPOSE 8080

CMD ["uvicorn", "adsb_proxy.main:app", "--host", "0.0.0.0", "--port", "8080"]
