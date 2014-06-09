import unittest
import pylons
import nose

import ckan.tests as tests
import ckanext.datastore.db as db


class TestTypeGetters(unittest.TestCase):
    def test_is_valid_field_name(self):
        assert db._is_valid_field_name("foo")
        assert db._is_valid_field_name("foo bar")
        assert db._is_valid_field_name("42")
        assert not db._is_valid_field_name('foo"bar')
        assert not db._is_valid_field_name('"')
        assert db._is_valid_field_name("'")
        assert not db._is_valid_field_name("")
        assert db._is_valid_field_name("foo%bar")

    def test_is_valid_table_name(self):
        assert db._is_valid_table_name("foo")
        assert db._is_valid_table_name("foo bar")
        assert db._is_valid_table_name("42")
        assert not db._is_valid_table_name('foo"bar')
        assert not db._is_valid_table_name('"')
        assert db._is_valid_table_name("'")
        assert not db._is_valid_table_name("")
        assert not db._is_valid_table_name("foo%bar")

    def test_pg_version_check(self):
        if not tests.is_datastore_supported():
            raise nose.SkipTest("Datastore not supported")
        engine = db._get_engine(
            {'connection_url': pylons.config['sqlalchemy.url']})
        connection = engine.connect()
        assert db._pg_version_is_at_least(connection, '8.0')
        assert not db._pg_version_is_at_least(connection, '10.0')

    def test_is_single_statement(self):
        singles = ['SELECT * FROM footable',
                   'SELECT * FROM "bartable"',
                   'SELECT * FROM "bartable";',
                   'SELECT * FROM "bart;able";',
                   "select 'foo'||chr(59)||'bar'"]

        multiples = ['SELECT * FROM abc; SET LOCAL statement_timeout to'
                     'SET LOCAL statement_timeout to; SELECT * FROM abc',
                     'SELECT * FROM "foo"; SELECT * FROM "abc"']

        for single in singles:
            assert db._is_single_statement(single) is True

        for multiple in multiples:
            assert db._is_single_statement(multiple) is False
