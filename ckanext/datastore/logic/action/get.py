import logging
import pylons
import ckan.logic as logic
import ckan.plugins as p
import ckanext.datastore.db as db

log = logging.getLogger(__name__)
_get_or_bust = logic.get_or_bust


def datastore_search(context, data_dict):
    '''Search a datastore table.

    :param resource_id: id of the data that is going to be selected.
    :type resource_id: string
    :param filters: matching conditions to select.
    :type filters: dictionary
    :param q: full text query
    :type q: string
    :param limit: maximum number of rows to return (default: 100)
    :type limit: int
    :param offset: offset the number of rows
    :type offset: int
    :param fields: ordered list of fields to return
                   (default: all fields in original order)
    :type fields: list of strings
    :param sort: comma separated field names with ordering
                 eg: "fieldname1, fieldname2 desc"
    :type sort: string

    :returns: a dictionary containing the search parameters and the
              search results.
              keys: fields: same as datastore_create accepts
                    offset: query offset value
                    limit: query limit value
                    filters: query filters
                    total: number of total matching records
                    records: list of matching results
    :rtype: dictionary

    '''
    model = _get_or_bust(context, 'model')
    id = _get_or_bust(data_dict, 'resource_id')

    if not model.Resource.get(id):
        raise p.toolkit.ObjectNotFound(p.toolkit._(
            'Resource "{}" was not found.'.format(id)
        ))

    p.toolkit.check_access('datastore_search', context, data_dict)

    data_dict['connection_url'] = pylons.config['ckan.datastore_write_url']

    result = db.search(context, data_dict)
    result.pop('id')
    result.pop('connection_url')
    return result
