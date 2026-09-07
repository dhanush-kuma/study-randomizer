#!/bin/sh
set -e

cd /app/backend

echo "Waiting for database and running migrations..."
attempt=0
max_attempts=30

while [ "$attempt" -lt "$max_attempts" ]; do
  if alembic upgrade head; then
    echo "Migrations complete."
    break
  fi
  attempt=$((attempt + 1))
  if [ "$attempt" -eq "$max_attempts" ]; then
    echo "Database migrations failed after ${max_attempts} attempts." >&2
    exit 1
  fi
  echo "Database not ready (attempt ${attempt}/${max_attempts}), retrying in 2s..."
  sleep 2
done

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
