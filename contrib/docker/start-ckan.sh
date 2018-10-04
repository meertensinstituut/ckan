#!/bin/bash
if [ ! -f .env ]; then
    echo "Creating new .env file! Please adapt it to your use case"
    cp .env.template .env
fi

# remove and copy the plugins from the latest codes - ckanext-facet
rm -fr ../../ckanext-facet/
echo "$?"
if [ "0" -eq "$?" ]; then
    echo "removed successfully ckanext-facet"
else
    echo "ckanext-facet not zero"
fi
cp -a ../../../code_dev/ckanext-facet/. ../../ckanext-facet/
if [ "0" -eq "$?" ]; then
    echo "copied successfully ckanext-facet"
fi

# remove and copy the plugins from the latest codes - ckanext-timeline
rm -fr ../../ckanext-timeline/
echo "$?"
if [ "0" -eq "$?" ]; then
    echo "removed successfully ckanext-timeline"
else
    echo "ckanext-timeline not zero"
fi
cp -a ../../../code_dev/ckanext-timeline/. ../../ckanext-timeline/
if [ "0" -eq "$?" ]; then
    echo "copied successfully ckanext-timeline"
fi

# remove and copy the ssl certificate
rm -fr ../../ssl/
echo "$?"
if [ "0" -eq "$?" ]; then
    echo "removed successfully ssl"
else
    echo "ssl not zero"
fi
sudo cp -a /etc/letsencrypt/live/search.isebel.eu/. ../../ssl/
if [ "0" -eq "$?" ]; then
    echo "copied successfully ssl"
fi

# Start docker
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
docker cp harvester/import_xml_to_ckan_wossidia.py ckan:/var/harvester/import_xml_to_ckan_wossidia.py
docker cp ../../../code_dev/translation-thesaurus ckan:/var/harvester/translation-thesaurus
