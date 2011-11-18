from nose.tools import assert_equal

import ckan
from ckan.lib.navl.dictization_functions import validate
import ckan.logic.schema

class TestPackage:
    def test_name_validation(self):
        context = {'model': ckan.model,
                   'session': ckan.model.Session}
        schema = ckan.logic.schema.default_package_schema()
        def get_package_name_validation_errors(package_name):
            data_dict = {'name': package_name}
            data, errors = validate(data_dict, schema, context)
            return errors.get('name', [])

        good_names = ('blah', 'ab', 'ab1', 'some-random-made-up-name', 'has_underscore', 'annakarenina')
        bad_names = (('', [u'Missing value']),
                     ('blAh', [u'Url must be purely lowercase alphanumeric (ascii) characters and these symbols: -_']),
                     ('a', [u'Name must be at least 2 characters long']),
                     ('dot.in.name', [u'Url must be purely lowercase alphanumeric (ascii) characters and these symbols: -_']),
                     (u'unicode-\xe0', [u'Url must be purely lowercase alphanumeric (ascii) characters and these symbols: -_']),
                     ('percent%', [u'Url must be purely lowercase alphanumeric (ascii) characters and these symbols: -_']),
#                     ('p'*101, [u'Too many characters]),
                     )

        for package_name in good_names:
            errors = get_package_name_validation_errors(package_name)
            assert_equal(errors, [])

        for package_name, expected_errors in bad_names:
            errors = get_package_name_validation_errors(package_name)
            errors = [err.replace('"%s"' % package_name, 'NAME') for err in errors]
            assert errors==expected_errors, \
                   '%r: %r != %r' % (package_name, errors, expected_errors)

class TestTag:
    def test_tag_name_validation(self):
        context = {'model': ckan.model}
        schema = ckan.logic.schema.default_tags_schema()
        def get_tag_validation_errors(tag_name):
            data_dict = {'name': tag_name}

            data, errors = validate(data_dict, schema, context)
            return errors.get('name', [])

        good_names = ('blah', 'ab', 'ab1', 'some-random-made-up-name',\
                      'has_underscore', u'unicode-\xe0', 'dot.in.name',\
                      'multiple words', u'with Greek omega \u03a9', 'CAPITALS')
        bad_names = (('a', [u'Tag TAG length is less than minimum 2']),
                     ('  ,leading comma', [u'Tag TAG must be alphanumeric characters or symbols: -_.']),
                     ('trailing comma,', [u'Tag TAG must be alphanumeric characters or symbols: -_.']),\
                     ('empty,,tag', [u'Tag TAG must be alphanumeric characters or symbols: -_.']),
                     ('quote"character', [u'Tag TAG must be alphanumeric characters or symbols: -_.']),
                     )

        for tag_name in good_names:
            errors = get_tag_validation_errors(tag_name)
            assert_equal(errors, [])

        for tag_name, expected_errors in bad_names:
            errors = get_tag_validation_errors(tag_name)
            errors = [err.replace('"%s"' % tag_name, 'TAG') for err in errors]
            assert_equal(errors, expected_errors)

    def test_tag_string_parsing(self):
        # 'tag_string' is what you type into the tags field in the package
        # edit form. This test checks that it is parsed correctly or reports
        # errors correctly.
        context = {'model': ckan.model,
                   'session': ckan.model.Session}
        schema = ckan.logic.schema.package_form_schema()

        # basic parsing of comma separated values
        tests = (('tag', ['tag'], []),
                 ('tag1, tag2', ['tag1', 'tag2'], []),
                 ('tag 1', ['tag 1'], []),
                 )
        for tag_string, expected_tags, expected_errors in tests:
            data_dict = {'tag_string': tag_string}
            data, errors = validate(data_dict, schema, context)
            assert_equal(errors.get('tags', []), expected_errors)
            tag_names = [tag_dict['name'] for tag_dict in data['tags']]
            assert_equal(tag_names, expected_tags)
            
        # test whitespace chars are stripped
        whitespace_characters = u'\t\n\r\f\v '
        for ch in whitespace_characters:
            tag = ch + u'tag name' + ch
            data_dict = {'tag_string': tag}
            data, errors = validate(data_dict, schema, context)
            assert_equal(data['tags'], [{'name': u'tag name'}])


