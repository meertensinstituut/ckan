import logging
import blinker

from ckan.model.notifier import DomainObjectNotification, Notification
from ckan.model import DomainObjectOperation
from ckan.lib.async_notifier import AsyncConsumer
from ckan.plugins import SingletonPlugin, implements, IDomainObjectNotification
from common import SearchError

log = logging.getLogger(__name__)

         
def dispatch_by_operation(entity_type, entity, operation, backend=None):
    """ Call the appropriate index method for a given notification. """
    if backend is None: 
        from ckan.lib.search import get_backend
        backend = get_backend()
    try:
        index = backend.index_for(entity)
        if operation == DomainObjectOperation.new:
            index.insert_dict(entity)
        elif operation == DomainObjectOperation.changed:
            index.update_dict(entity)
        elif operation == DomainObjectOperation.deleted:
            index.remove_dict(entity)
        else:
            log.warn("Unknown operation: %s" % operation)
    except Exception, ex:
        log.exception(ex)


class SynchronousSearchPlugin(SingletonPlugin):

    implements(IDomainObjectNotification, inherit=True)

    def notify(self, entity, operation):
        if hasattr(entity, 'as_dict'):
            dispatch_by_operation(entity.__class__.__name__, 
                                  entity.as_dict(), operation)
        else:
            log.warn("Discarded Sync. indexing for: %s" % entity)
            

