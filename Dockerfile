FROM python:2.7.12

COPY ./docker/prod/docker-helpers/install_consul_template.sh \
     ./docker/prod/docker-helpers/install_runit.sh \
     /usr/local/bin/
RUN chmod 755 /usr/local/bin/install_consul_template.sh /usr/local/bin/install_runit.sh && \
    sync && \
    install_consul_template.sh && \
    rm -f \
        /usr/local/bin/install_consul_template.sh \
        /usr/local/bin/install_runit.sh

################
# CAA Redirect #
################

RUN apt-get update && \
    apt-get install \
        --no-install-suggests \
        --no-install-recommends \
        -y \
        build-essential \
        libffi-dev \
        libssl-dev \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

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
ENTRYPOINT ["/usr/local/bin/runsvinit"]
