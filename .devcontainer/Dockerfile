# syntax=docker/dockerfile:1.4
ARG VARIANT="ubuntu-22.04"
FROM mcr.microsoft.com/devcontainers/base:${VARIANT}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git \
    gnupg \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libpq-dev \
    postgresql-client \
  && rm -rf /var/lib/apt/lists/*

ARG NODE_MAJOR=18
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash - \
  && apt-get update \
  && apt-get install -y --no-install-recommends nodejs \
  && rm -rf /var/lib/apt/lists/*

RUN corepack enable \
  && corepack prepare pnpm@8.6.12 --activate

# Install uv via pipx for Python tooling parity with CI
RUN python3 -m pip install --upgrade pip \
  && pip install --no-cache-dir uv==0.1.45

USER vscode
WORKDIR /workspace/vTOC

# Pre-create virtual environment for FastAPI backend
RUN python3 -m venv .venv \
  && echo '.venv/' >> /home/vscode/.gitignore_global \
  && git config --global core.excludesfile /home/vscode/.gitignore_global

ENV PATH="/workspace/vTOC/.venv/bin:${PATH}"

# Default to shell; devcontainer.json overrides with bootstrap commands
CMD ["sleep", "infinity"]
