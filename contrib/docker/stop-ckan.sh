#!/bin/bash

# kill and prune containers:
docker-compose stop
docker container prune -f
docker ps -a

# remove harvester
rm -rf harvester/harvester_src

# remove and copy the plugins from the latest codes - ckanext-facet
rm -fr ../../ckanext-facet/

# remove and copy the plugins from the latest codes - ckanext-isebelimporter
rm -fr ../../ckanext-isebelimporter/

# remove and copy the plugins from the latest codes - ckanext-isebeltranslate
rm -fr ../../ckanext-isebeltranslate/

# remove and copy the plugins from the latest codes - ckanext-timeline
rm -fr ../../ckanext-timeline/
