#!/bin/bash
set -e

# Function to stop the bot gracefully
stop_bot() {
    echo "Stopping bot gracefully..."
    kill -TERM "$pid" 2>/dev/null
    wait "$pid"
    exit 0
}

# Trap SIGTERM
trap stop_bot SIGTERM

# Wait for PostgreSQL
until python -c "import psycopg2; psycopg2.connect(host='${DB_HOST}', port=${DB_PORT}, user='${DB_USER}', password='${DB_PASSWORD}', dbname='${DB_NAME}')" 2>/dev/null; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

# Run migrations (skip if no migrations folder)
if [ -d "/app/migrations" ]; then
    echo "Running Alembic migrations..."
    alembic upgrade head
else
    echo "Skipping Alembic migrations (no migrations folder)"
fi

# Start the bot in background
echo "Starting the Telegram bot..."
python main.py &
pid=$!

# Wait for the bot process
wait "$pid"
