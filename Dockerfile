FROM python:3.12-slim
ENV POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update \
    && apt-get install --yes --no-install-recommends vim

WORKDIR code/
COPY . .

RUN pip install poetry

RUN poetry config installer.max-workers 10
RUN poetry install --no-interaction --no-ansi
RUN poetry run opentelemetry-bootstrap --action=install

ENV SECRET_KEY=built-only-not-used-at-runtime \
    DJANGO_SETTINGS_MODULE=thebook.settings

RUN poetry run python manage.py collectstatic --noinput

EXPOSE 8000
CMD poetry run opentelemetry-instrument gunicorn --bind :8000 --workers 2 thebook.wsgi
