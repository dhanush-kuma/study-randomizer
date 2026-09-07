# Multi-stage build: React frontend + FastAPI backend in one container.
# PostgreSQL is NOT included — add a Railway Postgres plugin and link DATABASE_URL.

# --- Frontend build ---
FROM node:22-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

# Same-origin deploy: API calls use relative URLs (e.g. /organizer/me).
ARG VITE_API_URL=
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# --- Backend runtime ---
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/dist ./frontend_dist
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENV FRONTEND_DIST=/app/frontend_dist
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
