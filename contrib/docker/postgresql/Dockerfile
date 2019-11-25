#FROM postgres:9.6
FROM mdillon/postgis:10
LABEL maintainer="Open Knowledge"

# Allow connections; we don't map out any ports so only linked docker containers can connect
RUN echo "host all  all    0.0.0.0/0  md5" >> /var/lib/postgresql/data/pg_hba.conf && \
unlink /etc/localtime && ln -s /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime

#RUN apt-get update && apt-get install python-dev libxml2-dev libxslt1-dev libgeos-c1 -y
RUN apt-get update && apt-get install python-dev libxml2-dev libxslt1-dev -y

# Customize default user/pass/db
ENV POSTGRES_DB ckan
ENV POSTGRES_USER ckan
ARG POSTGRES_PASSWORD
ARG DS_RO_PASS

# Include datastore setup scripts
ADD ./contrib/docker/postgresql/docker-entrypoint-initdb.d /docker-entrypoint-initdb.d
