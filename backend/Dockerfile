# Multi-stage build; same image is used for the API and every worker
# (Implementation Plan §14 — different startup commands per Cloud Run service).

FROM python:3.12-slim AS base

RUN groupadd --system app && useradd --system --gid app --create-home app

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY workers ./workers
COPY migrations ./migrations

RUN pip install --no-cache-dir .

USER app

EXPOSE 8000

# Default command runs the API. Worker services override this in their
# respective infrastructure/cloud-run/*.yaml startup command.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
