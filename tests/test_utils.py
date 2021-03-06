# -*- coding: utf-8 -*-

import os
import re
import sys
import tempfile
from types import GeneratorType

import pytest
import unicodecsv as csv

from dhis2 import exceptions, Api
from dhis2.utils import (
    load_csv,
    load_json,
    partition_payload,
    version_to_int,
    generate_uid,
    is_valid_uid,
    pretty_json,
    clean_obj
)

from .common import API_URL, BASEURL

PY3 = sys.version_info[0] == 3


@pytest.fixture  # BASE FIXTURE
def api():
    return Api(BASEURL, 'admin', 'district')


@pytest.fixture
def csv_file():
    content = [
        'abc,def',
        '1,2',
        '3,4',
        'ñ,äü'
    ]
    tmp = tempfile.gettempdir()
    filename = os.path.join(tmp, 'file.csv')

    with open(filename, 'wb') as f:
        w = csv.writer(f, delimiter=',')
        w.writerows([x.split(',') for x in content])
    yield filename
    os.remove(filename)


def test_load_csv(csv_file):
    expected = [
        {u"abc": u"1", "def": u"2"},
        {u"abc": u"3", "def": u"4"},
        {u"abc": u"ñ", "def": u"äü"}
    ]
    tmp = tempfile.gettempdir()
    filename = os.path.join(tmp, 'file.csv')
    loaded = list(load_csv(filename))
    assert loaded == expected
    for d in loaded:
        for k, v in d.items():
            if PY3:
                assert isinstance(k, str) and isinstance(v, str)
            else:
                assert isinstance(k, basestring) and isinstance(v, basestring)


def test_load_csv_not_found():
    with pytest.raises(exceptions.ClientException):
        for _ in load_csv('nothere.csv'):
            pass


def test_load_json_not_found():
    with pytest.raises(exceptions.ClientException):
        load_json('nothere.json')


@pytest.mark.parametrize("payload,threshold,expected", [
    (
            {"dataElements": [1, 2, 3, 4, 5, 6, 7, 8]},
            3,
            [
                {"dataElements": [1, 2, 3]},
                {"dataElements": [4, 5, 6]},
                {"dataElements": [7, 8]}
            ]
    ),
    (
            {"dataElements": [1, 2, 3, 4, 5, 6, 7, 8]},
            9,
            [
                {"dataElements": [1, 2, 3, 4, 5, 6, 7, 8]}
            ]
    )
])
def test_partition_payload(payload, threshold, expected):
    key = 'dataElements'
    c_gen = partition_payload(payload, key, threshold)
    assert isinstance(c_gen, GeneratorType)
    assert list(c_gen) == expected


@pytest.mark.parametrize("version,expected", [
    ("2.30", 30),
    ("2.30-SNAPSHOT", 30),
    ("2.30-RC1", 30),
    ("2.31.1", 31),
    ("2.31.2", 31),
    ("unknown", None)
])
def test_version_to_int(version, expected):
    assert version_to_int(version) == expected


def test_generate_uids():
    uid_regex = r"^[A-Za-z][A-Za-z0-9]{10}$"
    assert all([re.match(uid_regex, uid) for uid in [generate_uid() for _ in range(100000)]])


@pytest.mark.parametrize("uid_list,result", [
    ({'RAQaLoYJEuS', 'QTIquqiULFK', 'NqkDeV7vRTK', 'NyghHtH5oNm'}, True),
    ({'RAQaLoYJEu', '', None, 123456}, False),
])
def test_is_uid(uid_list, result):
    assert all([is_valid_uid(uid) is result for uid in uid_list])


@pytest.mark.parametrize("obj", [
    {'data': [1, 2, 3]},
    '{"pager": {"page": 1}}',
])
def test_pretty_json(capsys, obj):
    pretty_json(obj)
    out, err = capsys.readouterr()
    sys.stdout.write(out)
    sys.stderr.write(err)
    assert out.startswith("{")


@pytest.mark.parametrize("obj", [
    '',
    '{"pager": {"page": }}'
])
def test_pretty_json_not_json_string(obj):
    with pytest.raises(exceptions.ClientException):
        pretty_json(obj)


@pytest.mark.parametrize("obj,key_to_clean,expected", [
    (  # remove sharing
        {
            'dataElements': [{
                'id': 'abc',
                'publicAccess': '1',
                'userGroupAccesses': [1, 2, 3]
            }]
        },
        ["userGroupAccesses"],
        {
            'dataElements': [{
                'id': 'abc',
                'publicAccess': '1',
            }]
        }
    ),
    (  # nested dict still works
        {
            'dataElements': [{
                'id': 'abc',
                'publicAccess': '1',
                'userGroupAccesses': [{"userGroupAccesses": [1, 2, 3]}]
            }]
        },
        ["userGroupAccesses"],
        {
            'dataElements': [{
                'id': 'abc',
                'publicAccess': '1',
            }]
        }
    ),
    (  # works even with `remove` being just a string
            {
                'dataElements': [{
                    'id': 'abc',
                    'publicAccess': '1',
                    'userGroupAccesses': [1, 2, 3]
                }]
            },
            "userGroupAccesses",
            {
                'dataElements': [{
                    'id': 'abc',
                    'publicAccess': '1',
                }]
            }
    ),
    (  # works with no keys matching
            {
                'dataElements': [{
                    'id': 'abc',
                    'publicAccess': '1',
                }]
            },
            "notHere",
            {
                'dataElements': [{
                    'id': 'abc',
                    'publicAccess': '1',
                }]
            }
    ),
    ({}, {}, {}),
    ({}, 'justChecking', {}),
    (None, 'hello', None),
    ([[1, 3], (1, 2), [3]]),
])
def test_remove_keys(obj, key_to_clean, expected):
    assert clean_obj(obj, key_to_clean) == expected


@pytest.mark.parametrize("obj,key_to_clean,expected", [
    ([1, None, 1]),
    (
            {
                'a': 1,
                'b': 2
            },
            None,
            '_'
    ),
    (
            {
                None: 1,
                'b': 2
            },
            None,
            '_'
    ),
    (None, None, None)
])
def test_remove_keys_invalid(obj, key_to_clean, expected):
    with pytest.raises(exceptions.ClientException):
        _ = clean_obj(obj, key_to_clean) == expected
