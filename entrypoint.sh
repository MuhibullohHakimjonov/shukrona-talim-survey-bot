#!/bin/bash
# Wait for PostgreSQL to be ready using a Python check
until python -c "import psycopg2; psycopg2.connect(host='$DB_HOST', port='$DB_PORT', user='$DB_USER', password='$DB_PASSWORD', dbname='$DB_NAME')" 2>/dev/null; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

# Run Alembic migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Start the bot
echo "Starting the Telegram bot..."
python main.py