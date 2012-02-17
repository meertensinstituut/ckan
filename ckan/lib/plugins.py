import logging

from ckan.lib.base import model, c
from ckan.lib.navl.dictization_functions import DataError
from ckan.authz import Authorizer
import ckan.logic

from ckan.plugins import PluginImplementations, IDatasetForm, IGroupForm

log = logging.getLogger(__name__)

# Mapping from package-type strings to IDatasetForm instances
_package_plugins = {}
# The fallback behaviour
_default_package_plugin = None

# Mapping from group-type strings to IDatasetForm instances
_group_plugins = {}
# The fallback behaviour
_default_group_plugin = None


def lookup_package_plugin(package_type=None):
    """
    Returns the plugin controller associoated with the given package type.

    If the package type is None or cannot be found in the mapping, then the
    fallback behaviour is used.
    """
    if package_type is None:
        return _default_package_plugin
    return _package_plugins.get(package_type, _default_package_plugin)


def lookup_group_plugin(group_type=None):
    """
    Returns the plugin controller associoated with the given group type.

    If the group type is None or cannot be found in the mapping, then the
    fallback behaviour is used.
    """
    if group_type is None:
        return _default_group_plugin
    return _group_plugins.get(group_type, _default_group_plugin)


def register_package_plugins(map):
    """
    Register the various IDatasetForm instances.

    This method will setup the mappings between package types and the registered
    IDatasetForm instances.  If it's called more than once an
    exception will be raised.
    """
    global _default_package_plugin

    # Create the mappings and register the fallback behaviour if one is found.
    for plugin in PluginImplementations(IDatasetForm):
        if plugin.is_fallback():
            if _default_package_plugin is not None:
                raise ValueError, "More than one fallback "\
                                  "IDatasetForm has been registered"
            _default_package_plugin = plugin

        for package_type in plugin.package_types():
            # Create a connection between the newly named type and the package controller
            map.connect('/%s/new' % (package_type,), controller='package', action='new')
            map.connect('%s_read' % (package_type,), '/%s/{id}' %  (package_type,), controller='package', action='read')
            map.connect('%s_action' % (package_type,),
                        '/%s/{action}/{id}' % (package_type,), controller='package',
                requirements=dict(action='|'.join(['edit', 'authz', 'history' ]))
            )

            if package_type in _package_plugins:
                raise ValueError, "An existing IDatasetForm is "\
                                  "already associated with the package type "\
                                  "'%s'" % package_type
            _package_plugins[package_type] = plugin

    # Setup the fallback behaviour if one hasn't been defined.
    if _default_package_plugin is None:
        _default_package_plugin = DefaultDatasetForm()




def register_group_plugins(map):
    """
    Register the various IGroupForm instances.

    This method will setup the mappings between package types and the registered
    IGroupForm instances.  If it's called more than once an
    exception will be raised.
    """
    global _default_group_plugin

    # Create the mappings and register the fallback behaviour if one is found.
    for plugin in PluginImplementations(IGroupForm):
        if plugin.is_fallback():
            if _default_group_plugin is not None:
                raise ValueError, "More than one fallback "\
                                  "IGroupForm has been registered"
            _default_group_plugin = plugin

        for group_type in plugin.group_types():
            # Create the routes based on group_type here, this will allow us to have top level
            # objects that are actually Groups, but first we need to make sure we are not
            # clobbering an existing domain

            # Our version of routes doesn't allow the environ to be passed into the match call
            # and so we have to set it on the map instead.  This looks like a threading problem
            # waiting to happen but it is executed sequentially from instead the routing setup

            map.connect('%s_index' % (group_type,),
                        '/%s' % (group_type,), controller='group', action='index')
            map.connect('%s_new' % (group_type,),
                        '/%s/new' % (group_type,), controller='group', action='new')
            map.connect('%s_read' % (group_type,),
                        '/%s/{id}' %  (group_type,), controller='group', action='read')
            map.connect('%s_action' % (group_type,),
                        '/%s/{action}/{id}' % (group_type,), controller='group',
                requirements=dict(action='|'.join(['edit', 'authz', 'history' ]))
            )

            if group_type in _group_plugins:
                raise ValueError, "An existing IGroupForm is "\
                                  "already associated with the package type "\
                                  "'%s'" % group_type
            _group_plugins[group_type] = plugin

    # Setup the fallback behaviour if one hasn't been defined.
    if _default_group_plugin is None:
        _default_group_plugin = DefaultGroupForm()


class DefaultDatasetForm(object):
    """
    Provides a default implementation of the pluggable package controller behaviour.

    This class has 2 purposes:

     - it provides a base class for IDatasetForm implementations
       to use if only a subset of the 5 method hooks need to be customised.

     - it provides the fallback behaviour if no plugin is setup to provide
       the fallback behaviour.

    Note - this isn't a plugin implementation.  This is deliberate, as
           we don't want this being registered.
    """

    # this is to prevent import issues
    package_form_schema = None

    def package_form(self):
        return 'package/new_package_form.html'

    def form_to_db_schema(self):
        if not self.package_form_schema:
            from ckan.logic.schema import package_form_schema
            self.package_form_schema = package_form_schema
        return self.package_form_schema()

    def db_to_form_schema(self):
        '''This is an interface to manipulate data from the database
        into a format suitable for the form (optional)'''

    def check_data_dict(self, data_dict):
        '''Check if the return data is correct, mostly for checking out if
        spammers are submitting only part of the form'''

        # Resources might not exist yet (eg. Add Dataset)
        surplus_keys_schema = ['__extras', '__junk', 'state', 'groups',
                               'extras_validation', 'save', 'return_to',
                               'resources', 'type']

        schema_keys = self.form_to_db_schema().keys()
        keys_in_schema = set(schema_keys) - set(surplus_keys_schema)

        missing_keys = keys_in_schema - set(data_dict.keys())

        if missing_keys:
            #print data_dict
            #print missing_keys
            log.info('incorrect form fields posted, missing %s' % missing_keys )
            raise DataError(data_dict)

    def setup_template_variables(self, context, data_dict):
        c.groups_authz = ckan.logic.get_action('group_list_authz')(context, data_dict)
        data_dict.update({'available_only':True})
        c.groups_available = ckan.logic.get_action('group_list_authz')(context, data_dict)
        c.licences = [('', '')] + model.Package.get_license_options()
        c.is_sysadmin = Authorizer().is_sysadmin(c.user)

        ## This is messy as auths take domain object not data_dict
        context_pkg = context.get('package',None)
        pkg = context_pkg or c.pkg
        if pkg:
            try:
                if not context_pkg:
                    context['package'] = pkg
                ckan.logic.check_access('package_change_state',context)
                c.auth_for_change_state = True
            except ckan.logic.NotAuthorized:
                c.auth_for_change_state = False


class DefaultGroupForm(object):
    """
    Provides a default implementation of the pluggable Group controller behaviour.

    This class has 2 purposes:

     - it provides a base class for IGroupForm implementations
       to use if only a subset of the method hooks need to be customised.

     - it provides the fallback behaviour if no plugin is setup to provide
       the fallback behaviour.

    Note - this isn't a plugin implementation.  This is deliberate, as
           we don't want this being registered.
    """
    # prevent import issues
    group_form_schema = None

    def group_form(self):
        return 'group/new_group_form.html'

    def form_to_db_schema(self):
        if not self.group_form_schema:
            from ckan.logic.schema import group_form_schema
            self.group_form_schema = group_form_schema
        return self.group_form_schema()

    def db_to_form_schema(self):
        '''This is an interface to manipulate data from the database
        into a format suitable for the form (optional)'''


    def check_data_dict(self, data_dict):
        '''Check if the return data is correct, mostly for checking out if
        spammers are submitting only part of the form

        # Resources might not exist yet (eg. Add Dataset)
        surplus_keys_schema = ['__extras', '__junk', 'state', 'groups',
                               'extras_validation', 'save', 'return_to',
                               'resources']

        schema_keys = package_form_schema().keys()
        keys_in_schema = set(schema_keys) - set(surplus_keys_schema)

        missing_keys = keys_in_schema - set(data_dict.keys())

        if missing_keys:
            #print data_dict
            #print missing_keys
            log.info('incorrect form fields posted')
            raise DataError(data_dict)
        '''
        pass

    def setup_template_variables(self, context, data_dict):
        c.is_sysadmin = Authorizer().is_sysadmin(c.user)

        ## This is messy as auths take domain object not data_dict
        context_group = context.get('group',None)
        group = context_group or c.group
        if group:
            try:
                if not context_group:
                    context['group'] = group
                ckan.logic.check_access('group_change_state',context)
                c.auth_for_change_state = True
            except ckan.logic.NotAuthorized:
                c.auth_for_change_state = False
