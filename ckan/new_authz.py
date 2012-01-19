from logging import getLogger
from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IAuthFunctions
from ckan.plugins import PluginImplementations
from ckan.lib.base import _

log = getLogger(__name__)

# This is a private cache used by get_auth_function() and should never
# be accessed directly
_auth_functions = {}

def is_authorized(action, context,data_dict=None):
    
    # Ideally if we can find out if this is a publisher user (i.e. is part 
    # of a publisher) then we can add publisher_ to the front of the action
    # name to use the publisher auth instead of the standard one.
    
    auth_function = _get_auth_function(action)
    if auth_function:
        return auth_function(context, data_dict)
    else:
        raise ValueError(_('Authorization function not found: %s' % action))

def _get_auth_function(action):
    from pylons import config
            
    if _auth_functions:
        return _auth_functions.get(action)
        
    # Otherwise look in all the plugins to resolve all possible
    # First get the default ones in the ckan/logic/auth directory
    # Rather than writing them out in full will use __import__
    # to load anything from ckan.auth that looks like it might
    # be an authorisation function
    
    # We will load the auth profile from settings
    module_root = 'ckan.logic.auth'
    auth_profile = config.get('auth.profile', '')
    if auth_profile:
        module_root = '%s.%s' % (module_root, auth_profile)

    log.info('Using auth profile at %s' % module_root)
    
    for auth_module_name in ['get', 'create', 'update','delete']:
        module_path = '%s.%s' % (module_root, auth_module_name,)
        try:
            module = __import__(module_path)
            log.info('Loaded module %r' % module)
        except ImportError,e:
            print 'Failed to find auth module'
            log.debug('No auth module for action "%s"' % auth_module_name)
            continue

        for part in module_path.split('.')[1:]:
            module = getattr(module, part)
            
        for key, v in module.__dict__.items():
            if not key.startswith('_'):
                _auth_functions[key] = v

    # Then overwrite them with any specific ones in the plugins:
    resolved_auth_function_plugins = {}
    fetched_auth_functions = {}
    for plugin in PluginImplementations(IAuthFunctions):
        for name, auth_function in plugin.get_auth_functions().items():
            if name in resolved_auth_function_plugins:
                raise Exception(
                    'The auth function %r is already implemented in %r' % (
                        name,
                        resolved_auth_function_plugins[name]
                    )
                )
            log.debug('Auth function %r was inserted', plugin.name)
            resolved_auth_function_plugins[name] = plugin.name
            fetched_auth_functions[name] = auth_function
    # Use the updated ones in preference to the originals.
    _auth_functions.update(fetched_auth_functions)
    return _auth_functions.get(action)

