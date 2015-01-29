import logging

from ckan.common import json
import ckan.plugins as p
import ckanext.resourceproxy.plugin as proxy
import ckan.lib.datapreview as datapreview

log = logging.getLogger(__name__)

DEFAULT_TEXT_FORMATS = ['text/plain', 'txt', 'plain']
DEFAULT_XML_FORMATS = ['xml', 'rdf', 'rdf+xml', 'owl+xml', 'atom', 'rss']
DEFAULT_JSON_FORMATS = ['json']
DEFAULT_JSONP_FORMATS = ['jsonp']


class TextView(p.SingletonPlugin):
    '''This extension previews JSON(P).'''

    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IConfigurable, inherit=True)
    p.implements(p.IResourceView, inherit=True)
    p.implements(p.IPackageController, inherit=True)

    proxy_is_enabled = False
    text_formats = []
    xml_formats = []
    json_formats = []
    jsonp_formats = []
    no_jsonp_formats = []

    def update_config(self, config):
        text_formats = config.get('ckan.preview.text_formats', '').split()
        self.text_formats = text_formats or DEFAULT_TEXT_FORMATS

        xml_formats = config.get('ckan.preview.xml_formats', '').split()
        self.xml_formats = xml_formats or DEFAULT_XML_FORMATS

        json_formats = config.get('ckan.preview.json_formats', '').split()
        self.json_formats = json_formats or DEFAULT_JSON_FORMATS

        jsonp_formats = config.get('ckan.preview.jsonp_formats', '').split()
        self.jsonp_formats = jsonp_formats or DEFAULT_JSONP_FORMATS

        self.no_jsonp_formats = (self.text_formats +
                                 self.xml_formats +
                                 self.json_formats)

        p.toolkit.add_public_directory(config, 'theme/public')
        p.toolkit.add_template_directory(config, 'theme/templates')
        p.toolkit.add_resource('theme/public', 'ckanext-textview')

    def info(self):
        return {'name': 'text', 'title': 'Text', 'icon': 'file-text-alt'}

    def can_view(self, data_dict):
        resource = data_dict['resource']
        format_lower = resource['format'].lower()
        proxy_enabled = p.plugin_loaded('resource_proxy')
        same_domain = datapreview.on_same_domain(data_dict)
        if format_lower in self.jsonp_formats:
            return True
        if format_lower in self.no_jsonp_formats:
            if proxy_enabled or same_domain:
                return True
        return False

    def setup_template_variables(self, context, data_dict):
        metadata = {'text_formats': self.text_formats,
                    'json_formats': self.json_formats,
                    'jsonp_formats': self.jsonp_formats,
                    'xml_formats': self.xml_formats}

        url = proxy.get_proxified_resource_url(data_dict)
        format_lower = data_dict['resource']['format'].lower()
        if format_lower in self.jsonp_formats:
            url = data_dict['resource']['url']

        return {'preview_metadata': json.dumps(metadata),
                'resource_json': json.dumps(data_dict['resource']),
                'resource_url': json.dumps(url)}

    def view_template(self, context, data_dict):
        return 'text_view.html'

    def form_template(self, context, data_dict):
        return 'text_form.html'

    def add_default_views(self, context, data_dict):
        resources = datapreview.get_new_resources(context, data_dict)
        for resource in resources:
            if self.can_view({'package': data_dict, 'resource': resource}):
                format = resource.get('format', '')
                if format.lower() in ['csv', 'tsv']:
                    continue
                view = {
                    'title': 'Text View',
                    'description': 'View of the {format} file'.format(
                        format=format.upper()
                    ),
                    'resource_id': resource['id'],
                    'view_type': 'text'
                }
                p.toolkit.get_action('resource_view_create')(
                    {'defer_commit': True}, view
                )

    def after_update(self, context, data_dict):
        self.add_default_views(context, data_dict)

    def after_create(self, context, data_dict):
        self.add_default_views(context, data_dict)
