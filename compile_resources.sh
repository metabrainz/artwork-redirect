#!/bin/sh

cd "$(dirname $0)"
node_modules/.bin/lessc ./static/css/main.less > ./static/css/main.css
