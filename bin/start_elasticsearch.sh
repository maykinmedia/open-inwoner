docker pull docker.elastic.co/elasticsearch/elasticsearch:7.15.2
docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -m=1g docker.elastic.co/elasticsearch/elasticsearch:7.15.2
