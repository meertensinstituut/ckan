from ckan.tests import *
import ckan.lib.helpers as h
import ckan.logic as l
import ckan.model as model
from ckan.lib.create_test_data import CreateTestData
from ckan.tests.functional.base import FunctionalTestCase
import ckan.plugins as plugins
import ckan.tests.mock_plugin as mock
from ckan.lib.dictization.model_dictize import resource_dictize


class MockResourcePreviewExtension(mock.MockSingletonPlugin):
    plugins.implements(plugins.IResourcePreview)

    def __init__(self):
        from collections import defaultdict
        self.calls = defaultdict(int)

    def can_preview(self, data_dict):
        self.calls['can_preview'] += 1
        return data_dict['resource']['format'].lower() == 'mock'

    def setup_template_variables(self, context, data_dict):
        self.calls['setup_template_variables'] += 1

    def preview_template(self, context, data_dict):
        self.calls['preview_templates'] += 1
        return 'tests/mock_resource_preview_template.html'


class JsonMockResourcePreviewExtension(MockResourcePreviewExtension):
    def can_preview(self, data_dict):
        return data_dict['resource']['format'].lower() == 'json'

    def preview_template(self, context, data_dict):
        self.calls['preview_templates'] += 1
        return 'tests/mock_json_resource_preview_template.html'


class TestPluggablePreviews(FunctionalTestCase):
    @classmethod
    def setup_class(cls):
        cls.plugin = MockResourcePreviewExtension()
        plugins.load(cls.plugin)
        json_plugin = JsonMockResourcePreviewExtension()
        plugins.load(json_plugin)

        CreateTestData.create()

    @classmethod
    def teardown_class(cls):
        model.repo.rebuild_db()
        plugins.unload(cls.plugin)

    def test_hook(self):
        testpackage = model.Package.get('annakarenina')
        resource_dict = resource_dictize(testpackage.resources[0], {'model': model})
        resource_dict['format'] = 'mock'

        context = {
            'model': model,
            'session': model.Session,
            'user': model.User.get('testsysadmin').name
        }

        # no preview for type "plain text"
        preview_url = h.url_for(controller='package',
                action='resource_datapreview',
                id=testpackage.id,
                resource_id=testpackage.resources[0].id)
        result = self.app.get(preview_url, status=409)
        assert 'No preview' in result.body, result.body

        l.action.update.resource_update(context, resource_dict)

        #there should be a preview for type "json"
        preview_url = h.url_for(controller='package',
                action='resource_datapreview',
                id=testpackage.id,
                resource_id=testpackage.resources[0].id)
        result = self.app.get(preview_url, status=200)

        assert 'mock-preview' in result.body
        assert 'mock-preview.js' in result.body

        assert self.plugin.calls['can_preview'] == 2, self.plugin.calls
        assert self.plugin.calls['setup_template_variables'] == 1, self.plugin.calls
        assert self.plugin.calls['preview_templates'] == 1, self.plugin.calls

        # test whether the json preview is used
        preview_url = h.url_for(controller='package',
                action='resource_datapreview',
                id=testpackage.id,
                resource_id=testpackage.resources[1].id)
        result = self.app.get(preview_url, status=200)

        assert 'mock-json-preview' in result.body
        assert 'mock-json-preview.js' in result.body

        assert self.plugin.calls['can_preview'] == 3, self.plugin.calls
        assert self.plugin.calls['setup_template_variables'] == 1, self.plugin.calls
        assert self.plugin.calls['preview_templates'] == 1, self.plugin.calls
