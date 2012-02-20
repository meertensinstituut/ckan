from nose.tools import assert_equal

from ckan.tests import *
from ckan.tests.pylons_controller import PylonsTestCase
import ckan.model as model

class TestWebstoreController(TestController, PylonsTestCase):
    @classmethod
    def setup_class(cls):
        PylonsTestCase.setup_class()
        model.repo.init_db()
        CreateTestData.create()
        
    @classmethod
    def teardown_class(self):
        model.repo.rebuild_db()

    # TODO: do we test authz. In essence authz is same as for resource read /
    # edit which in turn is same as dataset read / edit and which is tested
    # extensively elsewhere ...
    def test_read(self):
        dataset = model.Package.by_name(CreateTestData.pkg_names[0])
        resource_id = dataset.resources[0].id
        offset = url_for('webstore_read', id=resource_id)
        res = self.app.get(offset)
        assert_equal(res.status, 200)
        assert_equal(res.body, resource_id)

    def test_update(self):
        dataset = model.Package.by_name(CreateTestData.pkg_names[0])
        resource_id = dataset.resources[0].id
        offset = url_for('webstore_write', id=resource_id)
        res = self.app.post(offset)
        assert res.status in [401,302]

