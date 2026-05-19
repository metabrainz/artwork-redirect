# Benchmarks

Measures response time for redirect and static file endpoints without following redirects.

## Prerequisites

The server must be running with test data loaded.

Start the database and load test data:

    $ docker compose -f docker/docker-compose.dev.yml up -d mbs_db_test
    $ docker compose -f docker/docker-compose.dev.yml exec -T mbs_db_test \
        psql -U postgres musicbrainz_test < test/add_data.sql

## Running

    $ uv run benchmarks/bench.py --serve

This starts the server automatically, runs the benchmark, and stops it.
To benchmark an already-running server, omit `--serve`:

    $ uv run benchmarks/bench.py --host 127.0.0.1 --port 8081 -n 100

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | 127.0.0.1 | Server host |
| `--port` | 8081 | Server port |
| `-n` / `--iterations` | 50 | Requests per endpoint |

## Endpoints tested

- `release/front`, `release/back`, `release/index` — cover art redirects
- `release-group/front` — release group cover art redirect
- `release/front (404)` — non-existent release
- `event/front` — event art redirect
- `/` — index HTML (static)
- `/robots.txt` — robots file (static)
- `/img/big_logo.svg` — SVG image (static)
