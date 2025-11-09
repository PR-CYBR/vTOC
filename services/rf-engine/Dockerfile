# RF Engine Dockerfile
# Based on GNU Radio 3.10 with SoapySDR and device drivers
# Non-root user, minimal privileges for security

FROM gnuradio/gnuradio:3.10-ubuntu22.04

LABEL org.opencontainers.image.source="https://github.com/PR-CYBR/vTOC"
LABEL org.opencontainers.image.description="PR-CYBR RF Engine - FISSURE-class RF for vTOC"
LABEL org.opencontainers.image.licenses="MIT"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # SoapySDR and device drivers
    soapysdr-tools \
    libsoapysdr-dev \
    soapysdr-module-all \
    # RTL-SDR
    rtl-sdr \
    librtlsdr-dev \
    # USRP
    libuhd-dev \
    uhd-host \
    # HackRF
    hackrf \
    libhackrf-dev \
    # LimeSDR
    liblimesuite-dev \
    limesuite \
    # Python and build tools
    python3-pip \
    python3-dev \
    python3-numpy \
    python3-scipy \
    # Other utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash rfengine && \
    mkdir -p /data/sigmf /models && \
    chown -R rfengine:rfengine /data /models

# Set working directory
WORKDIR /app

# Copy pyproject.toml and install dependencies
COPY pyproject.toml ./
RUN pip3 install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-root --no-interaction --no-ansi

# Copy application code
COPY --chown=rfengine:rfengine rfengine ./rfengine

# Switch to non-root user
USER rfengine

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Run the RF Engine server
CMD ["python3", "-m", "rfengine.main"]
