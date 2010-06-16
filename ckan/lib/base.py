"""The base Controller API

Provides the BaseController class for subclassing.
"""
import logging

from pylons import c, cache, config, g, request, response, session
from pylons.controllers import WSGIController
from pylons.controllers.util import abort, etag_cache, redirect_to, redirect
from pylons.decorators import jsonify, validate
from pylons.i18n import _, ungettext, N_, gettext
from pylons.templating import render_genshi as render

import ckan
import ckan.lib.helpers as h
import ckan.model as model

PAGINATE_ITEMS_PER_PAGE = 50

class ValidationException(Exception):
    pass

class BaseController(WSGIController):
    repo = model.repo
    log = logging.getLogger(__name__)

    def __before__(self, action, **params):
        # what is different between session['user'] and environ['REMOTE_USER']
        c.__version__ = ckan.__version__
        c.user = request.environ.get('REMOTE_USER', None)
        c.remote_addr = request.environ.get('REMOTE_ADDR', 'Unknown IP Address')
        if c.remote_addr == 'localhost' or c.remote_addr == '127.0.0.1':
            # see if it was proxied
            c.remote_addr = request.environ.get('HTTP_X_FORWARDED_FOR',
                    '127.0.0.1')
        if c.user:
            c.user = c.user.decode('utf8')
            c.author = c.user
        else:
            c.author = c.remote_addr
        c.author = unicode(c.author)

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            model.Session.remove()

    def _get_pkg(self, id):
        # Try to find a package id...
        pkg = model.Session.query(model.Package).get(id)
        if pkg == None:
            # ...otherwise try to find a package name.
            pkg = model.Package.by_name(id)
        return pkg
    # Todo: Make sure package names can't be changed to look like package IDs?

# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']
