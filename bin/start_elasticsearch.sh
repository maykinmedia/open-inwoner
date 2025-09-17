#!/bin/bash

ES_IMAGE=elasticsearch:9.0.3

docker pull $ES_IMAGE
docker run --rm \
    -p 9200:9200 -p 9300:9300 \
    -e "discovery.type=single-node" \
    -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
    -e "xpack.security.enabled=false" \
    -m=1g \
    $ES_IMAGE
