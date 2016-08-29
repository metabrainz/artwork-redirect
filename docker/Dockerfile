FROM python:2.7.12

RUN apt-get update \
    && apt-get install -y build-essential \
                          libpq-dev \
                          libffi-dev \
                          libssl-dev

# Node
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get install -y nodejs

RUN mkdir /code
WORKDIR /code

# Python dependencies
RUN pip install -U cffi
COPY requirements.txt /code/
RUN pip install -r requirements.txt

# Node dependencies
COPY package.json /code/
RUN npm install

COPY . /code/
RUN lessc ./static/css/main.less > ./static/css/main.css

CMD ["python", "coverart_redirect_server.py"]




WORKDIR /apps
RUN git clone https://github.com/metabrainz/coverart_redirect.git

RUN npm install -g less

WORKDIR /apps/coverart_redirect

RUN pip install -r requirements.txt

COPY coverart_redirect.conf /apps/coverart_redirect/

RUN lessc ./static/css/main.less > ./static/css/main.css

#RUN cp coverart_redirect.conf.dist coverart_redirect.conf
#RUN sed -i 's/user=musicbrainz_user/user=musicbrainz/g' coverart_redirect.conf
#RUN sed -i 's/name=musicbrainz_db/name=musicbrainz/g' coverart_redirect.conf
#RUN sed -i 's/host=localhost/host=postgres/g' coverart_redirect.conf

EXPOSE 8080


