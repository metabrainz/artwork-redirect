FROM postgres:9.5

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        postgresql-server-dev-9.5 \
        git-core \
        libxml2-dev \
        libicu-dev \
        libdb-dev \
        libpq-dev \
        libexpat1-dev

RUN mkdir /tmp/code

RUN git clone https://github.com/metabrainz/postgresql-musicbrainz-unaccent.git \
    /tmp/code/postgresql-musicbrainz-unaccent
WORKDIR /tmp/code/postgresql-musicbrainz-unaccent
RUN make && make install

RUN git clone https://github.com/metabrainz/postgresql-musicbrainz-collate.git \
    /tmp/code/postgresql-musicbrainz-collate
WORKDIR /tmp/code/postgresql-musicbrainz-collate
RUN make && make install

ADD extensions.sql /docker-entrypoint-initdb.d/
