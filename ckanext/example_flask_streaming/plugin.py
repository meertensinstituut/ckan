# encoding: utf-8

import os.path as path

from flask import Blueprint
import flask

import ckan.plugins as p
from ckan.common import streaming_response


def stream_string():
    u'''Stream may consist of any common content, like words'''
    def generate():
        for w in u'Hello World, this is served from an extension'.split():
            yield w
    return streaming_response(generate())


def stream_template(**kwargs):
    u'''You can stream big templates as well.'''
    tpl = flask.current_app.jinja_env.get_template(u'stream.html')
    gen = tpl.stream(kwargs)
    # pass integer into `enable_buffering` to control, how many 
    # tokens will consist in every response chunk. 
    gen.enable_buffering()
    return streaming_response(gen)


def stream_file():
    u'''File stream. Just do not close it until response finished'''
    f_path = path.join(
        path.dirname(path.abspath(__file__)), u'tests/10lines.txt')

    def gen():
        with open(f_path) as test_file:
            for line in test_file:
                yield line

    return streaming_response(gen())


def stream_context():
    u'''Additional argument keep request context from destroying'''
    html = u'''{{ request.args.var }}'''

    def gen():
        yield flask.render_template_string(html)

    return streaming_response(gen(), with_context=True)


def stream_without_context():
    u'''You'll definitely get error attempting to get request info.'''
    html = u'''{{ request.args.var }}'''

    def gen():
        yield flask.render_template_string(html)

    # `with_context` set to False by default. Thus, you cannot use
    # request context in this case.
    return streaming_response(gen())


class ExampleFlaskStreamingPlugin(p.SingletonPlugin):
    u'''
    An example plugin to demonstrate Flask streaming responses.
    '''
    p.implements(p.IBlueprint)

    def get_blueprint(self):
        u'''Return a Flask Blueprint object to be registered by the app.'''

        # Create Blueprint for plugin
        blueprint = Blueprint(self.name, self.__module__)
        blueprint.template_folder = u'templates'
        # Add plugin url rules to Blueprint object
        rules = [
            (u'/stream/string', u'stream_string', stream_string),
            (u'/stream/template/<int:count>', u'stream_template',
             stream_template),
            (u'/stream/template/', u'stream_template', stream_template),
            (u'/stream/file', u'stream_file', stream_file),
            (u'/stream/context', u'stream_context', stream_context),
            (u'/stream/without_context', u'stream_without_context',
             stream_without_context),
        ]
        for rule in rules:
            blueprint.add_url_rule(*rule)

        return blueprint
