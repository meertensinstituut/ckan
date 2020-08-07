#!/bin/bash

cp -a ../../../code_dev/harvester_src/. harvester/harvester_src/

if [[ ! -f .env ]]; then
    echo "Creating new .env file! Please adapt it to your use case"
    cp .env.template .env
fi

# remove and copy the plugins from the latest codes - ckanext-facet
cp -a ../../../code_dev/ckanext-facet/. ../../ckanext-facet/
if [[ "0" -eq "$?" ]]; then
    echo "copied successfully ckanext-facet"
fi

# remove and copy the plugins from the latest codes - ckanext-isebelimporter
#cp -a ../../../code_dev/ckanext-isebelimporter/. ../../ckanext-isebelimporter/
#if [[ "0" -eq "$?" ]]; then
#    echo "copied successfully ckanext-isebelimporter"
#fi

# remove and copy the plugins from the latest codes - ckanext-isebeltranslate
#cp -a ../../../code_dev/ckanext-isebeltranslate/. ../../ckanext-isebeltranslate/
#if [[ "0" -eq "$?" ]]; then
#    echo "copied successfully ckanext-isebeltranslate"
#fi

# remove and copy the plugins from the latest codes - ckanext-timeline
cp -a ../../../code_dev/ckanext-timeline/. ../../ckanext-timeline/
if [[ "0" -eq "$?" ]]; then
    echo "copied successfully ckanext-timeline"
fi

# remove and copy the ssl certificate
#sudo rm -fr ../../ssl/
#echo "$?"
#if [[ "0" -eq "$?" ]]; then
#    echo "removed successfully ssl"
#else
#    echo "ssl not zero"
#fi
#sudo cp -a /etc/letsencrypt/live/search.isebel.eu/. ../../ssl/
#if [[ "0" -eq "$?" ]]; then
#    echo "copied successfully ssl"
#fi

# Start docker
if [ -n "$1" ]; then
  if [ "$1" == "all" ]; then
    echo "rebuilding all"
    docker-compose up -d --build
  else
    echo "rebuilding '$1'"
    docker-compose up -d --build "$1"
  fi
else
  echo "restarting"
  docker-compose up -d
fi

#docker-compose up -d --build ckan
# sleep 10
# docker-compose restart ckan
# sleep 10
# docker-compose restart ckan

# docker exec -it db /docker-entrypoint-initdb.d/00_create_datastore.sh
# docker exec ckan /usr/local/bin/ckan-paster --plugin=ckan datastore set-permissions -c /etc/ckan/production.ini | docker exec -i db psql -U ckan

# docker exec -it ckan /usr/local/bin/ckan-paster --plugin=ckan sysadmin -c /etc/ckan/production.ini add ckan_admin

docker cp harvester/import_xml_to_ckan.py ckan:/var/harvester/import_xml_to_ckan.py
docker cp harvester/import_xml_to_ckan_util.py ckan:/var/harvester/import_xml_to_ckan_util.py
docker cp harvester/testxmlvalidate.py ckan:/var/harvester/testxmlvalidate.py
docker cp ../../../code_dev/isebel-schema ckan:/var/harvester
docker cp ckanbashrc ckan:/usr/lib/ckan/.bashrc
#docker cp ../../../code_dev/translation-thesaurus ckan:/var/harvester/translation-thesaurus
docker cp translations ckan:/var/harvester/translations
