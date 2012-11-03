from logging import getLogger

import ckan.plugins as p
import ckan.lib.base as base

log = getLogger(__name__)


def get_proxified_resource_url(data_dict):
    '''
    :param data_dict: contains a resource and package dict
    :type data_dict: dictionary
    '''
    url = base.h.url_for(
        action='proxy_resource',
        controller='ckanext.resourceproxy.controller:ProxyController',
        id=data_dict['package']['name'],
        resource_id=data_dict['resource']['id'])
    log.info('Proxified url is {0}'.format(url))
    return url


class ResourceProxy(p.SingletonPlugin):
    """A proxy for CKAN resources to get around the same
    origin policy for previews

    This extension implements two interfaces

      - ``IRoutes`` allows to add a route to the proxy action
    """
    p.implements(p.IRoutes, inherit=True)

    def before_map(self, m):
        m.connect('/dataset/{id}/resource/{resource_id}/proxy',
                    controller='ckanext.resourceproxy.controller:ProxyController',
                    action='proxy_resource')
        return m
