#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
until python -c "import psycopg2; psycopg2.connect(host='${DB_HOST}', port=${DB_PORT}, user='${DB_USER}', password='${DB_PASSWORD}', dbname='${DB_NAME}')" 2>/dev/null; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

# Run Alembic migrations
echo "Running Alembic migrations..."
alembic upgrade head || echo "Alembic migration skipped (no migrations folder?)"

# Start the bot
echo "Starting the Telegram bot..."
python main.py
