Artwork URL redirect service
============================

This service will redirect from `coverartarchive.org` and `eventartarchive.org` URLs
to `archive.org` URLs, taking into account MBID redirects caused by release and event merges.

For example, this URL:

    https://coverartarchive.org/release/5b07fe49-39a9-47a6-97b3-e5005992fb2a/front.jpg

should redirect to:

    https://archive.org/download/mbid-5b07fe49-39a9-47a6-97b3-e5005992fb2a/mbid-5b07fe49-39a9-47a6-97b3-e5005992fb2a-2270157148.jpg

## Development setup

There are two ways of setting up the server: with and without Docker.
The first option might be easier if you're just getting started. The second
requires having a MusicBrainz database set up on your machine.

### Option 1: Docker-based

Make sure you have [Docker](https://www.docker.com/) and
[Docker Compose](https://github.com/docker/compose) installed.
To start the development server and its dependencies, run:

    $ docker compose -f docker/docker-compose.dev.yml up --build

After all Docker images start you should be able to access the web server at `localhost:8080`.

**Note:** Keep in mind that any changes that you make won't show up until the
server container is recreated. To do that you can simply stop the server
(Ctrl + C) and run the command above again.

### Option 2: Manual

artwork-redirect works with *Python 3.10+*. Install
[uv](https://docs.astral.sh/uv/getting-started/installation/), then:

    $ uv sync

Copy *config.default.ini* to *config.ini* and adjust configuration values.
You'd want to set up a connection to the instance of PostgreSQL with a
MusicBrainz database that you should already have running.

Run the server:

    $ uv run python artwork_redirect_server.py

All logging goes to stdout, including stacktraces, so it's suitable for
running inside of daemontools.

## Testing

Run the full test suite (requires Docker):

    $ docker compose -f docker/docker-compose.test.yml up --build

This starts a PostgreSQL container with MusicBrainz test data and runs
all tests against it.

**Note:** Tests cannot run without the database — `uv run pytest` alone
will fail with configuration errors.

## Development

    $ uv sync --group dev
    $ pre-commit install

    $ uv run ruff check .
    $ uv run ruff format .
    $ uv run pytest
