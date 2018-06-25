#!/bin/bash

# kill and prune containers:
docker kill ckan
docker kill db
docker kill datapusher
docker kill solr
docker kill redis
docker kill harvester

docker container prune -f

docker ps -a 
