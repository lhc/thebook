FROM python:3.11-slim
ENV POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update \
    && apt-get install --yes --no-install-recommends vim

WORKDIR code/
COPY . .

RUN pip install poetry

RUN poetry config installer.max-workers 10
RUN poetry install --no-interaction --no-ansi

EXPOSE 8000
CMD poetry run gunicorn --bind :8000 --workers 2 thebook.wsgi
