FROM python:3
WORKDIR /usr/app

# Python config
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installing poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Installing dependencies
COPY poetry.lock pyproject.toml /usr/app/
RUN poetry update -vvv --only main --no-ansi --no-interaction
RUN poetry install -vvv --only main --no-root --no-ansi --no-interaction

# Installing app
COPY README.md /usr/app/
COPY src/ /usr/app/src/
RUN poetry install -vvv --only-root --no-ansi --no-interaction
