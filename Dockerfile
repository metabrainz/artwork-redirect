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

RUN mkdir /code
WORKDIR /code

# Python dependencies
RUN apt-get update && \
    apt-get install -y \
            build-essential \
            libpq-dev \
            libffi-dev \
            libssl-dev
RUN pip install -U cffi
COPY requirements.txt /code/
RUN pip install -r requirements.txt

# Node dependencies
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get install -y nodejs
RUN npm install -g less less-plugin-clean-css

COPY . /code/
RUN lessc ./static/css/main.less > ./static/css/main.css

############
# Services #
############

# Consul-template is already installed with install_consul_template.sh
COPY ./docker/prod/redirect.service /etc/sv/redirect/run
RUN chmod 755 /etc/sv/redirect/run && \
    ln -sf /etc/sv/redirect /etc/service/

# Configuration
COPY ./docker/prod/consul-template.conf /etc/consul-template.conf

EXPOSE 62080
ENTRYPOINT ["/usr/local/bin/runsvinit"]
