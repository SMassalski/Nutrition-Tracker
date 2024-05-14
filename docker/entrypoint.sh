#!/bin/bash

echo "Waiting for the database..."

# Check for listening daemons (without sending data)
while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 0.1
done

echo "Database is available. Continuing..."

# Execute a command if provided in arguments
# "./entrypoint command arg1 arg2" calls "command arg1 arg2"
exec "$@"
