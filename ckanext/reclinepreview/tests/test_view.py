import mock
import paste.fixture
import pylons.config as config

import ckan.model as model
import ckan.tests as tests
import ckan.plugins as p
import ckan.lib.helpers as h
import ckanext.reclinepreview.plugin as previewplugin
import ckan.lib.create_test_data as create_test_data
import ckan.config.middleware as middleware


class TestReclinePreview(object):
    @classmethod
    def setup_class(cls):
        cls.plugins = ['recline_grid', 'recline_graph', 'recline_map']

        for plugin in cls.plugins:
            if p.plugin_loaded(plugin):
                p.unload(plugin)

    @classmethod
    def teardown_class(cls):
        p.load_all(config)

    def teardown(self):
        for plugin in ['recline_preview'] + self.plugins:
            if p.plugin_loaded(plugin):
                p.unload(plugin)

    def test_loads_all_recline_plugins_when_its_loaded(self):
        p.load('recline_preview')

        for plugin in self.plugins:
            assert p.plugin_loaded(plugin), "%s wasn't loaded" % plugin

    def test_doesnt_try_to_load_already_loaded_plugins(self):
        p.load('recline_grid')
        p.load('recline_map')

        p.load('recline_preview')

        for plugin in self.plugins:
            assert p.plugin_loaded(plugin), "%s wasn't loaded" % plugin

    @mock.patch('logging.getLogger')
    def test_loading_this_plugin_gives_a_warning(self, getLogger):
        log = mock.MagicMock()
        getLogger.return_value = log

        p.load('recline_preview')

        log.warn.assert_called_once()

    def test_this_plugin_only_exists_on_ckan_2_3(self):
        error_msg = ("Plugin 'resource_preview' plugin was created just to "
                     "ease the transition between 2.2 and 2.3. It should be "
                     "removed in later versions.")

        assert p.toolkit.check_ckan_version('2.4', '2.3'), error_msg


class BaseTestReclineView(tests.WsgiAppCase):
    @classmethod
    def setup_class(cls):
        cls.config_templates = config['ckan.legacy_templates']
        config['ckan.legacy_templates'] = 'false'
        wsgiapp = middleware.make_app(config['global_conf'], **config)
        p.load(cls.view_type)

        cls.app = paste.fixture.TestApp(wsgiapp)
        cls.p = cls.view_class()

        create_test_data.CreateTestData.create()

        cls.resource_view, cls.package, cls.resource_id = \
            _create_test_view(cls.view_type)

    @classmethod
    def teardown_class(cls):
        config['ckan.legacy_templates'] = cls.config_templates
        p.unload(cls.view_type)
        model.repo.rebuild_db()

    def test_can_preview(self):
        data_dict = {'resource': {'datastore_active': True}}
        assert self.p.can_view(data_dict)

        data_dict = {'resource': {'datastore_active': False}}
        assert not self.p.can_view(data_dict)

    def test_title_description_iframe_shown(self):
        url = h.url_for(controller='package', action='resource_read',
                        id=self.package.name, resource_id=self.resource_id)
        result = self.app.get(url)
        assert self.resource_view['title'] in result
        assert self.resource_view['description'] in result
        assert 'data-module="data-viewer"' in result.body


class TestReclineGrid(BaseTestReclineView):
    view_type = 'recline_grid'
    view_class = previewplugin.ReclineGrid

    def test_it_has_no_schema(self):
        schema = self.p.info().get('schema')
        assert schema is None, schema


class TestReclineGraph(BaseTestReclineView):
    view_type = 'recline_graph'
    view_class = previewplugin.ReclineGraph

    def test_it_has_the_correct_schema_keys(self):
        schema = self.p.info().get('schema')
        expected_keys = ['offset', 'limit', 'graph_type', 'group', 'series']
        _assert_schema_exists_and_has_keys(schema, expected_keys)


class TestReclineMap(BaseTestReclineView):
    view_type = 'recline_map'
    view_class = previewplugin.ReclineMap

    def test_it_has_the_correct_schema_keys(self):
        schema = self.p.info().get('schema')
        expected_keys = ['offset', 'limit', 'map_field_type',
                         'latitude_field', 'longitude_field', 'geojson_field',
                         'auto_zoom', 'cluster_markers']
        _assert_schema_exists_and_has_keys(schema, expected_keys)


def _create_test_view(view_type):
    context = {'model': model,
               'session': model.Session,
               'user': model.User.get('testsysadmin').name}

    package = model.Package.get('annakarenina')
    resource_id = package.resources[1].id
    resource_view = {'resource_id': resource_id,
                     'view_type': view_type,
                     'title': u'Test View',
                     'description': u'A nice test view'}
    resource_view = p.toolkit.get_action('resource_view_create')(
        context, resource_view)
    return resource_view, package, resource_id


def _assert_schema_exists_and_has_keys(schema, expected_keys):
    assert schema is not None, schema

    keys = schema.keys()
    keys.sort()
    expected_keys.sort()

    assert keys == expected_keys, '%s != %s' % (keys, expected_keys)
