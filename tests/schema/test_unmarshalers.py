# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

import pytest
import pytz

from falcon_oas.oas.schema.unmarshalers import SchemaUnmarshaler
from falcon_oas.oas.spec import create_spec_from_dict


@pytest.fixture
def schema():
    return {}


@pytest.fixture
def spec(schema):
    return create_spec_from_dict({'a': {'b': schema}})


@pytest.fixture
def reference():
    return {'$ref': '#/a/b'}


@pytest.mark.parametrize(
    'schema_type,instance',
    [
        ('boolean', True),
        ('boolean', False),
        ('number', 0.0),
        ('number', 2.0),
        ('integer', 0),
        ('integer', 2),
        ('string', 'foo'),
    ],
)
def test_unmarshal_atom(spec, schema, reference, schema_type, instance):
    schema['type'] = schema_type
    unmarshaled = SchemaUnmarshaler(spec).unmarshal(instance, reference)
    assert unmarshaled == instance


def test_unmarshal_atom_format_date(spec, schema, reference):
    schema.update({'type': 'string', 'format': 'date'})
    instance = '2018-01-02'
    unmarshaled = SchemaUnmarshaler(spec).unmarshal(instance, reference)
    assert unmarshaled == datetime.date(2018, 1, 2)


def test_unmarshal_atom_format_date_time(spec, schema, reference):
    schema.update({'type': 'string', 'format': 'date-time'})
    instance = '2018-01-02T03:04:05Z'
    unmarshaled = SchemaUnmarshaler(spec).unmarshal(instance, reference)
    assert unmarshaled == datetime.datetime(
        2018, 1, 2, 3, 4, 5, tzinfo=pytz.utc
    )


def test_unmarshal_atom_format_uri(spec, schema, reference):
    schema.update({'type': 'string', 'format': 'uri'})
    instance = 'http://example.com/path'
    unmarshaled = SchemaUnmarshaler(spec).unmarshal(instance, reference)
    assert unmarshaled == instance


def test_unmarshal_array(spec, schema, reference):
    schema.update(
        {'type': 'array', 'items': {'type': 'string', 'format': 'date'}}
    )
    instance = ['2018-01-02', '2018-02-03', '2018-03-04']
    unmarshaled = SchemaUnmarshaler(spec).unmarshal(instance, reference)
    assert unmarshaled == [
        datetime.date(2018, 1, 2),
        datetime.date(2018, 2, 3),
        datetime.date(2018, 3, 4),
    ]


def test_unmarshal_object(spec, schema, reference):
    schema.update(
        {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'date': {'type': 'string', 'format': 'date'},
                'date-default': {
                    'type': 'string',
                    'format': 'date',
                    'default': '2020-01-01',
                },
            },
        }
    )
    instance = {'date': '2018-01-02'}
    unmarshaled = SchemaUnmarshaler(spec).unmarshal(instance, reference)
    assert unmarshaled == {
        'date': datetime.date(2018, 1, 2),
        'date-default': datetime.date(2020, 1, 1),
    }


def test_unmarshal_object_without_properties(spec, schema, reference):
    schema['type'] = 'object'
    instance = {'date': '2018-01-02'}
    unmarshaled = SchemaUnmarshaler(spec).unmarshal(instance, reference)
    assert unmarshaled == {}


def test_unmarshal_all_of(spec, schema, reference):
    schema['allOf'] = [
        {'type': 'object', 'properties': {'id': {'type': 'integer'}}},
        {
            'type': 'object',
            'properties': {'date': {'type': 'string', 'format': 'date'}},
        },
    ]
    instance = {'id': 2, 'date': '2018-01-02'}
    unmarshaled = SchemaUnmarshaler(spec).unmarshal(instance, reference)
    assert unmarshaled == {'id': 2, 'date': datetime.date(2018, 1, 2)}


@pytest.mark.parametrize('schema_type', [('oneOf',), ('anyOf',)])
def test_unmarshal_one_of_or_any_of(spec, schema, reference, schema_type):
    schema[schema_type] = [
        {'type': 'string', 'format': 'date'},
        {'type': 'integer'},
    ]
    instance = '2018-01-02'
    unmarshaled = SchemaUnmarshaler(spec).unmarshal(instance, reference)
    assert unmarshaled == instance


def test_unmarshal_without_parsers(spec, schema, reference):
    schema.update({'type': 'string', 'format': 'date'})
    instance = '2018-01-02'
    unmarshaled = SchemaUnmarshaler(spec, parsers={}).unmarshal(
        instance, reference
    )
    assert unmarshaled == instance