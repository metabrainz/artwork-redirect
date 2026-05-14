FROM metabrainz/python:3.13-20260216

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
                       build-essential \
                       git \
                       libpq-dev \
                       libffi-dev \
                       libssl-dev \
                       sudo \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN useradd --create-home --shell /bin/bash art

WORKDIR /home/art/artwork-redirect
RUN chown art:art /home/art/artwork-redirect

COPY . ./
RUN chown -R art:art ./
RUN sudo -E -H -u art uv sync --frozen --no-dev --no-editable

############
# Services #
############

COPY ./docker/prod/redirect.service /etc/service/redirect/run
COPY ./docker/prod/uwsgi.ini /etc/uwsgi/

RUN chmod 755 /etc/service/redirect/run

# Configuration
COPY ./docker/prod/consul-template-redirect.conf /etc/

EXPOSE 8080
