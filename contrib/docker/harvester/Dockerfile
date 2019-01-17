FROM openjdk:8
LABEL maintainer="Vic  Ding <qiqing.ding@di.huc.knaw.nl>"

ADD harvester_src /tmp/harvester_src

RUN apt-get update && apt-get install maven git vim net-tools -y

ADD log4j2.xml /tmp/harvester_src/src/main/resources/log4j2.xml
RUN cd /tmp/harvester_src && mvn clean install -Dmaven.test.skip=true

ADD do-harvester.sh /tmp/harvester_src/src/main/scripts/do-harvester.sh
ADD run-harvester2.sh /tmp/harvester_src/src/main/scripts/run-harvester2.sh
ADD config-isebel.xml /tmp/harvester_src/src/main/scripts/config-isebel.xml

RUN chmod +x /tmp/harvester_src/src/main/scripts/*.sh
