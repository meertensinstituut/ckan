FROM openjdk:latest
LABEL maintainer="Vic <qiqing.ding@di.huc.knaw.nl>"

RUN apt-get update && apt-get install maven git vim net-tools -y && \
    cd /tmp && git clone -b 0.5.x https://github.com/clarin-eric/oai-harvest-manager.git harvester_src && \
    cd harvester_src && mvn clean install 
ADD do-harvester.sh /tmp/harvester_src/src/main/scripts/do-harvester.sh
ADD run-harvester2.sh /tmp/harvester_src/src/main/scripts/run-harvester2.sh
ADD config-isebel.xml /tmp/harvester_src/src/main/scripts/config-isebel.xml

RUN chmod +x /tmp/harvester_src/src/main/scripts/*.sh
