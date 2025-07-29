#!/bin/sh
set -e

# 1. Waits for the PostgreSQL database to be available.
echo "Waiting for DB at ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"; do
  sleep 2
done

# 2. Applies all Alembic migrations to update the DB schema.
echo "DB ready. Applying migrations..."
alembic -c alembic.ini upgrade head

# 3. Seeds initial data into the DB.
echo "Seeding initial data..."
python -m app.seed_user || echo "User seed skipped"
python -m app.seed_group_types || echo "Group types seed skipped"

# 4. Starts the FastAPI app using Uvicorn.
echo "Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000