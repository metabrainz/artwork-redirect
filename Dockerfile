FROM metabrainz/python:2.7

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

# Consul-template is already installed with install_consul_template.sh
COPY ./docker/prod/redirect.service /etc/sv/redirect/run
RUN chmod 755 /etc/sv/redirect/run && \
    ln -sf /etc/sv/redirect /etc/service/

# Configuration
COPY ./docker/prod/consul-template.conf /etc/consul-template.conf

EXPOSE 8080
