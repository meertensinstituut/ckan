"""
Tests for plugin loading via PCA
"""
import os
from unittest import TestCase
from pyutilib.component.core import PluginGlobals
from pylons import config
from pkg_resources import working_set, Distribution, PathMetadata
from ckan import plugins
from ckan.lib.create_test_data import CreateTestData


# Create the ckantestplugin setuptools distribution
mydir = os.path.dirname(__file__)
egg_info = os.path.join(mydir, 'ckantestplugin', 'ckantestplugin.egg-info')
base_dir = os.path.dirname(egg_info)
metadata = PathMetadata(base_dir, egg_info)
dist_name = os.path.splitext(os.path.basename(egg_info))[0]
ckantestplugin_dist = Distribution(base_dir, project_name=dist_name, metadata=metadata)


class TestPlugins(TestCase):

    def setUp(self):
        plugins.deactivate_all()
        self._saved_plugins_config = config.get('ckan.plugins')
        config['ckan.plugins'] = ''
        working_set.add(ckantestplugin_dist)

    def tearDown(self):
        # Ideally this would remove the ckantestplugin_dist from the working
        # set, but I can't find a way to do that in setuptools.
        plugins.deactivate_all()
        config['ckan.plugins'] = self._saved_plugins_config

    def test_plugins_load(self):

        config['ckan.plugins'] = 'mapper_plugin routes_plugin'
        plugins.load_all(config)

        # Imported after call to plugins.load_all to ensure that we test the
        # plugin loader starting from a blank slate.
        from ckantestplugin import MapperPlugin, RoutesPlugin

        assert PluginGlobals.env().services == set([MapperPlugin(), RoutesPlugin()])
        from ckan.model.extension import PluginMapperExtension
        assert list(PluginMapperExtension.observers) == [MapperPlugin()]

        from ckan.config.routing import routing_plugins
        assert list(routing_plugins) == [RoutesPlugin()]

    def test_only_configured_plugins_loaded(self):

        config['ckan.plugins'] = 'mapper_plugin'
        plugins.load_all(config)

        from ckantestplugin import MapperPlugin, RoutesPlugin
        from ckan.model.extension import PluginMapperExtension
        from ckan.config.routing import routing_plugins

        assert PluginGlobals.env().services == set([MapperPlugin()])
        assert list(PluginMapperExtension.observers) == [MapperPlugin()]
        assert list(routing_plugins) == []
