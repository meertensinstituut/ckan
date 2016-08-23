# encoding: utf-8

from paste.deploy.converters import asbool

import ckan.model as model
from ckan.common import g, request, config
from ckan.lib.helpers import redirect_to as redirect
import ckan.plugins as p

import logging
log = logging.getLogger(__name__)

APIKEY_HEADER_NAME_KEY = u'apikey_header_name'
APIKEY_HEADER_NAME_DEFAULT = u'X-CKAN-API-Key'


def set_cors_headers_for_response(response):
    u'''
    Set up Access Control Allow headers if either origin_allow_all is True, or
    the request Origin is in the origin_whitelist.
    '''
    if config.get('ckan.cors.origin_allow_all') \
       and request.headers.get('Origin'):

        cors_origin_allowed = None
        if asbool(config.get(u'ckan.cors.origin_allow_all')):
            cors_origin_allowed = "*"
        elif config.get(u'ckan.cors.origin_whitelist') and \
                request.headers.get(u'Origin') \
                in config[u'ckan.cors.origin_whitelist'].split(' '):
            # set var to the origin to allow it.
            cors_origin_allowed = request.headers.get(u'Origin')

        if cors_origin_allowed is not None:
            response.headers[u'Access-Control-Allow-Origin'] = \
                cors_origin_allowed
            response.headers[u'Access-Control-Allow-Methods'] = \
                u'POST, PUT, GET, DELETE, OPTIONS'
            response.headers[u'Access-Control-Allow-Headers'] = \
                u'X-CKAN-API-KEY, Authorization, Content-Type'


def identify_user():
    u'''Try to identify the user
    If the user is identified then:
      g.user = user name (unicode)
      g.userobj = user object
      g.author = user name
    otherwise:
      g.user = None
      g.userobj = None
      g.author = user's IP address (unicode)

    Note: Remember, when running under Pylons, `g` is the Pylons `c` object
    '''
    # see if it was proxied first
    g.remote_addr = request.environ.get(u'HTTP_X_FORWARDED_FOR', u'')
    if not g.remote_addr:
        g.remote_addr = request.environ.get(u'REMOTE_ADDR',
                                            u'Unknown IP Address')

    # Authentication plugins get a chance to run here break as soon as a user
    # is identified.
    authenticators = p.PluginImplementations(p.IAuthenticator)
    if authenticators:
        for item in authenticators:
            item.identify()
            if g.user:
                break

    # We haven't identified the user so try the default methods
    if not getattr(g, u'user', None):
        _identify_user_default()

    # If we have a user but not the userobj let's get the userobj. This means
    # that IAuthenticator extensions do not need to access the user model
    # directly.
    if g.user and not getattr(g, u'userobj', None):
        g.userobj = model.User.by_name(g.user)

    # general settings
    if g.user:
        g.author = g.user
    else:
        g.author = g.remote_addr
    g.author = unicode(g.author)


def _identify_user_default():
    u'''
    Identifies the user using two methods:
    a) If they logged into the web interface then repoze.who will
       set REMOTE_USER.
    b) For API calls they may set a header with an API key.
    '''

    # environ['REMOTE_USER'] is set by repoze.who if it authenticates a
    # user's cookie. But repoze.who doesn't check the user (still) exists
    # in our database - we need to do that here. (Another way would be
    # with an userid_checker, but that would mean another db access.
    # See: http://docs.repoze.org/who/1.0/narr.html#module-repoze.who\
    # .plugins.sql )
    g.user = request.environ.get(u'REMOTE_USER', u'')
    if g.user:
        g.user = g.user.decode(u'utf8')
        g.userobj = model.User.by_name(g.user)

        if g.userobj is None or not g.userobj.is_active():

            # This occurs when a user that was still logged in is deleted, or
            # when you are logged in, clean db and then restart (or when you
            # change your username). There is no user object, so even though
            # repoze thinks you are logged in and your cookie has
            # ckan_display_name, we need to force user to logout and login
            # again to get the User object.

            ev = request.environ
            if u'repoze.who.plugins' in ev:
                pth = getattr(ev[u'repoze.who.plugins'][u'friendlyform'],
                              u'logout_handler_path')
                redirect(pth)
    else:
        g.userobj = _get_user_for_apikey()
        if g.userobj is not None:
            g.user = g.userobj.name


def _get_user_for_apikey():
    apikey_header_name = config.get(APIKEY_HEADER_NAME_KEY,
                                    APIKEY_HEADER_NAME_DEFAULT)
    apikey = request.headers.get(apikey_header_name, u'')
    if not apikey:
        apikey = request.environ.get(apikey_header_name, u'')
    if not apikey:
        # For misunderstanding old documentation (now fixed).
        apikey = request.environ.get(u'HTTP_AUTHORIZATION', u'')
    if not apikey:
        apikey = request.environ.get(u'Authorization', u'')
        # Forget HTTP Auth credentials (they have spaces).
        if u' ' in apikey:
            apikey = u''
    if not apikey:
        return None
    log.debug(u'Received API Key: %s' % apikey)
    apikey = unicode(apikey)
    query = model.Session.query(model.User)
    user = query.filter_by(apikey=apikey).first()
    return user
