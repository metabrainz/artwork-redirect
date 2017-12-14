FROM metabrainz/python:3.6-1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
                       build-essential \
                       git \
                       libpq-dev \
                       libffi-dev \
                       libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /code
WORKDIR /code

# Python dependencies
RUN pip install -U cffi
COPY requirements.txt /code/
RUN pip install -r requirements.txt

# Node dependencies
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get install -y nodejs
COPY ./package.json /code/
RUN npm install

COPY . /code/
RUN ./node_modules/.bin/lessc ./static/css/main.less > ./static/css/main.css

############
# Services #
############

COPY ./docker/prod/redirect.service /etc/service/redirect/run
COPY ./docker/prod/uwsgi.ini /etc/uwsgi/

RUN chmod 755 /etc/service/redirect/run

# Configuration
COPY ./docker/prod/consul-template-redirect.conf /etc/

EXPOSE 8080
