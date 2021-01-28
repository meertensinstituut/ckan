# See CKAN docs on installation from Docker Compose on usage
FROM debian:stretch
LABEL maintainer="Open Knowledge"

# Install required system packages
RUN apt-get -q -y update \
    && DEBIAN_FRONTEND=noninteractive apt-get -q -y upgrade \
    && apt-get -q -y install \
        python-dev \
        python-pip \
        python-virtualenv \
        python-wheel \
        python3-dev \
        python3-pip \
        python3-virtualenv \
        python3-wheel \
        libpq-dev \
        libxml2-dev \
        libxslt-dev \
        libgeos-dev \
        libssl-dev \
        libffi-dev \
        postgresql-client \
        build-essential \
        git-core \
        vim \
        wget \
        net-tools \
    && apt-get -q clean \
    && rm -rf /var/lib/apt/lists/*

# Define environment variables
ENV CKAN_HOME /usr/lib/ckan
ENV CKAN_VENV $CKAN_HOME/venv
ENV CKAN_CONFIG /etc/ckan
ENV CKAN_STORAGE_PATH=/var/lib/ckan

# Build-time variables specified by docker-compose.yml / .env
ARG CKAN_SITE_URL

# Set correct timezone
RUN unlink /etc/localtime && ln -s /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime

# Create ckan user
RUN useradd -r -u 900 -m -c "ckan account" -d $CKAN_HOME -s /bin/false ckan

# Setup virtual environment for CKAN
RUN mkdir -p $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH && \
    virtualenv $CKAN_VENV && \
    ln -s $CKAN_VENV/bin/pip /usr/local/bin/ckan-pip &&\
    ln -s $CKAN_VENV/bin/paster /usr/local/bin/ckan-paster &&\
    ln -s $CKAN_VENV/bin/ckan /usr/local/bin/ckan

# Setup CKAN
ADD . $CKAN_VENV/src/ckan/
RUN ckan-pip install -U pip && \
    ckan-pip install --upgrade --no-cache-dir -r $CKAN_VENV/src/ckan/requirement-setuptools.txt && \
    ckan-pip install --upgrade --no-cache-dir -r $CKAN_VENV/src/ckan/requirements-py2.txt && \
    ckan-pip install -e $CKAN_VENV/src/ckan/ && \
    ckan-pip install ckanapi && \
    ckan-pip install ckantoolkit && \
    ckan-pip install flask-debugtoolbar && \
    ln -s /usr/lib/ckan/venv/bin/ckanapi /usr/local/bin/ckanapi && \
    ln -s $CKAN_VENV/src/ckan/ckan/config/who.ini $CKAN_CONFIG/who.ini && \
    cp -v $CKAN_VENV/src/ckan/contrib/docker/ckan-entrypoint.sh /ckan-entrypoint.sh && \
    chmod +x /ckan-entrypoint.sh && \
    chown -R ckan:ckan $CKAN_HOME $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH

RUN . $CKAN_VENV/bin/activate && ls -la $CKAN_VENV/src/ckan && \
    cd $CKAN_VENV/src/ckan/ckanext-facet && python setup.py develop && \
    cd $CKAN_VENV/src/ckan/ckanext-timeline && python setup.py develop && \
    ckan-pip install -e "git+https://github.com/ckan/ckanext-spatial.git#egg=ckanext-spatial" && \
    ckan-pip install --upgrade --no-cache-dir -r $CKAN_VENV/src/ckanext-spatial/pip-requirements.txt  && \
    cd $CKAN_VENV/src/ckanext-spatial && python setup.py develop && \
     ckan-pip install ckanext-geoview && \
    cd $CKAN_VENV/src/ && git clone https://github.com/ckan/ckanext-geoview.git && cd $CKAN_VENV/src/ckanext-geoview && python setup.py develop && \
    chown -R ckan:ckan $CKAN_HOME $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH && \
    deactivate
#ADD contrib/docker/production.ini /etc/ckan/production.ini

ENTRYPOINT ["/ckan-entrypoint.sh"]

USER ckan
EXPOSE 5000

CMD ["ckan","-c","/etc/ckan/production.ini", "run", "--host", "0.0.0.0"]
