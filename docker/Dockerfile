FROM debian:jessie

ARG DEBIAN_FRONTEND="noninteractive"

ENV LANG C.UTF-8

RUN apt-get update && apt-get install -y \
    apt-utils

RUN apt-get install -y \
  git-core \
  python-pip \
  build-essential \
  libpq-dev \
  python-dev \
  libffi-dev \
  curl

RUN curl -sL https://deb.nodesource.com/setup_4.x | bash -

RUN apt-get install -y nodejs

WORKDIR /apps
RUN git clone https://github.com/metabrainz/coverart_redirect.git

RUN npm install -g less

WORKDIR /apps/coverart_redirect
RUN pip install -U cffi
RUN pip install -r requirements.txt

COPY coverart_redirect.conf /apps/coverart_redirect/

RUN lessc ./static/css/main.less > ./static/css/main.css

#RUN cp coverart_redirect.conf.dist coverart_redirect.conf
#RUN sed -i 's/user=musicbrainz_user/user=musicbrainz/g' coverart_redirect.conf
#RUN sed -i 's/name=musicbrainz_db/name=musicbrainz/g' coverart_redirect.conf
#RUN sed -i 's/host=localhost/host=postgres/g' coverart_redirect.conf

EXPOSE 8080

CMD ["python", "coverart_redirect_server.py"]
