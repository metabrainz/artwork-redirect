#!/bin/sh

cd "$(dirname $0)"
node_modules/.bin/lessc --clean-css ./static/css/main.less > ./static/css/main.css
