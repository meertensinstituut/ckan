#!/bin/bash
if [ ! -f .env ]; then
    echo "Creating new .env file! Please adapt it to your use case"
    cp .env.template .env
fi

rm -fr ../../../ckan/ckanext-facet/
cp -a ../../../code_dev/ckanext-facet/. ../../../ckan/ckanext-facet/

docker-compose up -d --build 
# sleep 10
# docker-compose restart ckan
# sleep 10
# docker-compose restart ckan

# docker exec -it db /docker-entrypoint-initdb.d/00_create_datastore.sh
# docker exec ckan /usr/local/bin/ckan-paster --plugin=ckan datastore set-permissions -c /etc/ckan/production.ini | docker exec -i db psql -U ckan

# docker exec -it ckan /usr/local/bin/ckan-paster --plugin=ckan sysadmin -c /etc/ckan/production.ini add ckan_admin

docker cp harvester/import_xml_to_ckan_ucla.py ckan:/var/harvester/import_xml_to_ckan_ucla.py
docker cp harvester/import_xml_to_ckan.py ckan:/var/harvester/import_xml_to_ckan.py
docker cp ../../../code_dev/translation-thesaurus ckan:/var/harvester/translation-thesaurus