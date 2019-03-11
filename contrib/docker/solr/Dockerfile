FROM solr:6.6.5
LABEL maintainer="Open Knowledge"
ARG SOLR_VERSION=6.6.5

# Enviroment
ENV SOLR_CORE ckan
ENV SOLR_HEAP=2048m

# Create Directories
RUN mkdir -p /opt/solr/server/solr/$SOLR_CORE/conf
RUN mkdir -p /opt/solr/server/solr/$SOLR_CORE/data

# Adding Files
ADD ./contrib/docker/solr/solrconfig.xml \
./ckan/config/solr/schema.xml \
https://raw.githubusercontent.com/apache/lucene-solr/releases/lucene-solr/$SOLR_VERSION/solr/server/solr/configsets/basic_configs/conf/currency.xml \
https://raw.githubusercontent.com/apache/lucene-solr/releases/lucene-solr/$SOLR_VERSION/solr/server/solr/configsets/basic_configs/conf/synonyms.txt \
https://raw.githubusercontent.com/apache/lucene-solr/releases/lucene-solr/$SOLR_VERSION/solr/server/solr/configsets/basic_configs/conf/stopwords.txt \
https://raw.githubusercontent.com/apache/lucene-solr/releases/lucene-solr/$SOLR_VERSION/solr/server/solr/configsets/basic_configs/conf/protwords.txt \
https://raw.githubusercontent.com/apache/lucene-solr/releases/lucene-solr/$SOLR_VERSION/solr/server/solr/configsets/data_driven_schema_configs/conf/elevate.xml \
#https://raw.githubusercontent.com/apache/lucene-solr/releases/lucene-solr/7.5.0/solr/server/solr/configsets/sample_techproducts_configs/conf/currency.xml \
#https://raw.githubusercontent.com/apache/lucene-solr/releases/lucene-solr/7.5.0/solr/server/solr/configsets/sample_techproducts_configs/conf/synonyms.txt \
#https://raw.githubusercontent.com/apache/lucene-solr/releases/lucene-solr/7.5.0/solr/server/solr/configsets/sample_techproducts_configs/conf/stopwords.txt \
#https://raw.githubusercontent.com/apache/lucene-solr/releases/lucene-solr/7.5.0/solr/server/solr/configsets/sample_techproducts_configs/conf/protwords.txt \
#https://raw.githubusercontent.com/apache/lucene-solr/releases/lucene-solr/7.5.0/solr/server/solr/configsets/sample_techproducts_configs/conf/elevate.xml \
/opt/solr/server/solr/$SOLR_CORE/conf/

RUN ls -la /opt/solr/server/solr/$SOLR_CORE/conf/

# Create Core.properties
RUN echo name=$SOLR_CORE > /opt/solr/server/solr/$SOLR_CORE/core.properties

# Giving ownership to Solr

USER root
RUN chown -R $SOLR_USER:$SOLR_USER /opt/solr/server/solr/$SOLR_CORE && \
unlink /etc/localtime && ln -s /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime

# install JTS in order to use solr-spatial-field to accept geometry Point and Square
RUN apt-get update && apt-get install libjts-java -y && \
    cp /usr/share/java/jts.jar /opt/solr/server/solr-webapp/webapp/WEB-INF/lib/jts.jar && \
    cp /usr/share/java/jts-1.14.jar /opt/solr/server/solr-webapp/webapp/WEB-INF/lib/jts-1.14.jar
#RUN apt-get update && apt-get install libjts-java -y && \
#    cp /usr/share/java/jts-core.jar /opt/solr/server/solr-webapp/webapp/WEB-INF/lib/jts.jar && \
#    cp /usr/share/java/jts-app.jar /opt/solr/server/solr-webapp/webapp/WEB-INF/lib/jts-app.jar && \
#    cp /usr/share/java/jts-io-common.jar /opt/solr/server/solr-webapp/webapp/WEB-INF/lib/jts-io-common.jar

# User
USER $SOLR_USER:$SOLR_USER

