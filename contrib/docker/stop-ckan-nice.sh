#!/bin/bash

# kill and prune containers:
docker kill ckan
docker kill db
docker kill datapusher
docker kill solr
docker kill redis
docker kill harvester

docker rm ckan
docker rm db
docker rm datapusher
docker rm solr
docker rm redis
docker rm harvester

docker ps -a 
