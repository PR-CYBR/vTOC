# Station Playbooks

This directory contains onboarding guides, automation scripts, and seed data utilities for each vTOC station. Every station folder includes:

- A README that summarizes the mission profile, data domains, and integration touchpoints.
- An `onboard.sh` helper for applying Alembic migrations against the station schema.
- A lightweight `seed.py` utility that can populate canonical telemetry fixtures for local development and testing.

> **Tip:** Export the appropriate `DATABASE_URL_TOC_SX` environment variable before running onboarding scripts to target remote infrastructure.
