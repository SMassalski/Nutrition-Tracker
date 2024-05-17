# --- Static build ---
FROM node:22-bullseye as static-build
WORKDIR /app

COPY package.json package-lock.json webpack.config.js /app/
RUN npm install

COPY src/nutrition_tracker/assets /app/src/nutrition_tracker/assets
RUN npm run build

# --- Venv build ---
FROM python:3.11-bullseye as venv-build
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"
RUN poetry config virtualenvs.in-project true

# Install dependencies
# Separated for caching
COPY poetry.lock pyproject.toml /app/
RUN poetry update -vvv --only main --no-ansi --no-interaction
RUN poetry install -vvv --only main --no-root --no-ansi --no-interaction

# Install app
COPY src/ /app/src/
RUN poetry install -vvv --only-root --no-ansi --no-interaction

# --- Final build ---
FROM python:3.11-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update

# Install psycopg dependencies
RUN apt-get install -y libpq-dev gcc

# nc is used to check if the database is available
RUN apt-get install -y netcat-openbsd

WORKDIR /app/src/nutrition_tracker

# Copy entrypoint script
COPY ./docker/entrypoint.sh .
RUN chmod +x ./entrypoint.sh

COPY --from=venv-build /app /app
# Static after venv to ensure that the built files are not overwritten
COPY --from=static-build /app/src/nutrition_tracker/static /app/src/nutrition_tracker/static

# Add venv to the path
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT [ "./entrypoint.sh" ]
