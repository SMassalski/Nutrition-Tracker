#!/bin/bash

# Commands that should be ran when the environment is started for the
# first time.

set -e

docker compose -f docker/docker-compose.yml exec app python manage.py collectstatic --no-input --clear
docker compose -f docker/docker-compose.yml exec app python manage.py migrate --no-input

echo
echo "Create a Superuser"
echo

docker compose -f docker/docker-compose.yml exec -it app python manage.py createsuperuser

# Uncomment this if you want to load the built-in nutrient
# and recommendation data.
#docker compose -f docker/docker-compose.yml exec app python manage.py loadnutrientdata

# Uncomment this if you want to load FDC ingredient data if there is any
# in the data folder.
#docker compose -f docker/docker-compose.yml cp data app:/app/data
#docker compose -f docker/docker-compose.yml exec app python manage.py loadfdcdata
