# -*- coding: utf-8 -*-

import re
import logging

import ckan.plugins as plugins
from ckan.common import config
from ckanext.datastore.interfaces import IDatastoreBackend

log = logging.getLogger(__name__)


def get_all_resources_ids_in_datastore():
    """
    Helper for getting id of all resources in datastore.

    Uses `get_all_ids` of active datastore backend.
    """
    DatastoreBackend.register_backends()
    DatastoreBackend.set_active_backend(config)
    backend = DatastoreBackend.get_active_backend()
    backend.configure(config)

    return backend.get_all_ids()


def _parse_sort_clause(clause, fields_types):
    clause_match = re.match(u'^(.+?)( +(asc|desc) *)?$', clause, re.I)

    if not clause_match:
        return False

    field = clause_match.group(1)
    if field[0] == field[-1] == u'"':
        field = field[1:-1]
    sort = (clause_match.group(3) or u'asc').lower()

    if field not in fields_types:
        return False

    return field, sort


class DatastoreException(Exception):
    pass


class InvalidDataError(Exception):
    """Exception that's raised if you try to add invalid data to the datastore.

    For example if you have a column with type "numeric" and then you try to
    add a non-numeric value like "foo" to it, this exception should be raised.

    """
    pass


class DatastoreBackend:
    """Base class for all datastore backends.

    Very simple example of implementation based on SQLite can be found in
    `ckanext.datastore.backend.example`. In order to use it, set datastore.write_url
    to 'example-sqlite:////tmp/database-name-on-your-choice'

    :prop _backend: mapping(schema, class) of all registered backends
    :type _backend: dictonary
    :prop _active_backend: current active backend
    :type _active_backend: DatastoreBackend
    """

    _backends = {}
    _active_backend = None

    @classmethod
    def register_backends(cls):
        """Register all backend implementations inside extensions."""
        for plugin in plugins.PluginImplementations(IDatastoreBackend):
            cls._backends.update(plugin.register_backends())

    @classmethod
    def set_active_backend(cls, config):
        """Choose most suitable backend depending on configuration

        :param config: configuration object
        :rtype: ckan.common.CKANConfig

        """
        schema = config.get('ckan.datastore.write_url').split(':')[0]
        cls._active_backend = cls._backends[schema]()

    @classmethod
    def get_active_backend(cls):
        """Return currently used backend"""
        return cls._active_backend

    def configure(self, config):
        """Configure backend, set inner variables, make some initial setup.

        :param config: configuration object
        :returns: config
        :rtype: CKANConfig

        """

        return config

    def create(self, context, data_dict):
        """Create new resourct inside datastore.

        Called by `datastore_create`.
        """

        raise NotImplementedError()

    def upsert(self, context, data_dict):
        """Update or create resource depending on data_dict param.

        Called by `datastore_upsert`.
        """
        raise NotImplementedError()

    def delete(self, context, data_dict):
        """Remove resource from datastore.

        Called by `datastore_delete`.
        """
        raise NotImplementedError()

    def search(self, context, data_dict):
        """Base search.

        Called by `datastore_search`.
        """
        raise NotImplementedError()

    def search_sql(self, context, data_dict):
        """Advanced search.

        Called by `datastore_search_sql`.
        """
        raise NotImplementedError()

    def make_private(self, context, data_dict):
        """Do not display resource in search results.

        Called by `datastore_make_private`.
        """
        raise NotImplementedError()

    def make_public(self, context, data_dict):
        """Enable serch for resource.

        Called by `datastore_make_public`.
        """
        raise NotImplementedError()

    def resource_exists(self, id):
        """Define whether resource exists in datastore.
        """
        raise NotImplementedError()

    def resource_fields(self, id):
        """Return dictonary with resource description.

        Called by `datastore_info`.
        :returns: dictonary with nested dicts `schema` and `meta`
        """
        raise NotImplementedError()

    def resource_info(self, id):
        """Return DataDictonary with resource's info - #3414
        """
        raise NotImplementedError()

    def resource_id_from_alias(self, alias):
        """Convert resource's alias to real id.
        """
        raise NotImplementedError()

    def get_all_ids(self):
        """Return id of all resource registered in datastore.
        """
        raise NotImplementedError()
