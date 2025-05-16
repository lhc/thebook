[![🔨 Deploy on fly.io](https://github.com/lhc/thebook/actions/workflows/flyio.yml/badge.svg)](https://github.com/lhc/thebook/actions/workflows/flyio.yml)
[![📅 Schedule Categorization](https://github.com/lhc/thebook/actions/workflows/categorize.yml/badge.svg)](https://github.com/lhc/thebook/actions/workflows/categorize.yml)
[![💰 Monthly Receivable Fees](https://github.com/lhc/thebook/actions/workflows/receivable_fees.yml/badge.svg)](https://github.com/lhc/thebook/actions/workflows/receivable_fees.yml)

# The Book

Application for administrative control of
[*Laboratório Hacker de Campinas*](https://lhc.net.br), a hackerspace located in
[Campinas, SP, Brazil](https://www.openstreetmap.org/search?query=Laborat%C3%B3rio%20Hacker%20de%20Campinas#map=19/-22.91780/-47.05245).

It is a (not complete) single-entry bookkeeping system with some particularities
that are suitable for accounting management of the hackerspace.
However, we believe that this application can be used by any small association that
wants to track the origin and the destination of the money received.

## Main Features

- Modified single-entry bookkeeping system with some particularities that are suitable for accounting
  management of our hackerspace.
- Document management of financial transactions

# Development

You need to install the following tools to start developing in the project:

- [pyenv](https://github.com/pyenv/pyenv) to manage your Python version and create isolated
  environment where you can safely develop;
- [poetry](https://python-poetry.org/) for packaging and dependency management
- [pre-commit](https://pre-commit.com/) to run code formatter and linter before commits

## Local Environment

Run the following command in the root directory of the project. The execution of this command
will create a virtual environment and install all required dependencies needed for development.

```
poetry install
```

Now you need to activate the virtual environment so you can start developing. You need to
execute this step before any other described in this document:

```
eval $(poetry env activate)
```

Enable your `pre-commit` hooks:

```
pre-commit install
```

### Running

Before running the application locally for the first time (or after creating a
new database migration), you need to run the following command:

```
task migrate
```

You can start the application it using the following command:

```
task run
```

Then you should be able to access it at http://127.0.0.1:8000

To create a superuser to have access to Django Admin (http://127.0.0.1:8000/admin),
use the following command and answer its questions:

```
python manage.py createsuperuser
```

## Deployment

Application is running in a [fly.io](https://fly.io/) account. If you are planning to
update the production version, ask some member of LHC board to get access credentials.
Our account username is `contato@lhc.net.br`.

See [Django docs](https://docs.djangoproject.com/en/5.0/howto/deployment/) if you want to deploy
in a different platform.

Production database is a self-managed PostgreSQL. You need to set `DATABASE_URL` setting with
the credentials of your own database. For development, the default is to use a SQLite database
file.

### Authentication

Before start using [fly.io](https://fly.io/), you need to authenticate with the right credentials. Use the command bellow and follow the instructions:

```
$ flyctl auth login
```

### Configuration

To set/update the environment variables to configure the applications (secret keys,
database URL, etc.), you can use fly.io dashboard or use the following command for
each variable you want to set:

```
flyctl secrets set VARIABLE_NAME="value"
```

You can see the list of secrets configured using the command:

```
flyctl secrets list
```

You can also set environment variables that will be deployed in `[env]` section
of `fly.toml`. **Don't commit any value that shouldn't be public (like database credentials)**


### Production Deploy

When everything is configured as desired, deploy to production using the command:

```
flyctl deploy --verbose
```

### Useful commands

- Application status

```
flyctl status
```

- Application logs

```
flyctl logs
```

- Application console

```
flyctl ssh console -C bash
```

> If you see the error message `Error: app thebook has no started VMs.` it means
> that there is no machine running the application. Just access the application in
> your browser (so a new VM is started) and try again.
