import json

import pytest
import responses

from dhis2 import Dhis, exceptions

BASEURL = 'https://play.dhis2.org/2.29'
API_URL = '{}/api'.format(BASEURL)


@pytest.mark.parametrize("status_code", [
    400, 401, 402, 403, 404, 405, 406, 407, 408, 409,
    410, 411, 412, 413, 414, 415, 416, 417, 418, 421,
    422, 423, 424, 426, 428, 429, 431, 451, 444, 494,
    495, 496, 497, 499, 500, 501, 502, 503, 504, 505,
    506, 507, 508, 510, 511
])
@responses.activate
def test_client_server_errors(status_code):
    url = '{}/dataElements/foo.json'.format(API_URL)

    responses.add(responses.GET, url, body='something failed', status=status_code)

    api = Dhis(BASEURL, 'admin', 'district')
    with pytest.raises(exceptions.APIException) as e:
        api.get(endpoint='dataElements/foo')
    assert e.value.code == status_code
    assert e.value.url == url
    assert e.value.description == 'something failed'
    assert str(e.value)
    assert repr(e.value)

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == url


@responses.activate
def test_post():
    url = '{}/metadata'.format(API_URL)
    p = {"obj": "some data"}

    responses.add(responses.POST, url, json=p, status=201)

    api = Dhis(BASEURL, 'admin', 'district')
    api.post(endpoint='metadata', data=p)

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == url


@responses.activate
def test_put():
    url = '{}/organisationUnits/uid'.format(API_URL)
    p = {"obj": "some data"}

    responses.add(responses.PUT, url, json=p, status=200)

    api = Dhis(BASEURL, 'admin', 'district')
    api.put(endpoint='organisationUnits/uid', data=p)

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == url


@responses.activate
def test_patch():
    url = '{}/organisationUnits/uid'.format(API_URL)
    p = {"obj": "some data"}

    responses.add(responses.PATCH, url, json=p, status=200)

    api = Dhis(BASEURL, 'admin', 'district')
    api.patch(endpoint='organisationUnits/uid', data=p)

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == url


@responses.activate
def test_delete():
    url = '{}/organisationUnits/uid'.format(API_URL)

    responses.add(responses.DELETE, url, status=200)

    api = Dhis(BASEURL, 'admin', 'district')
    api.delete(endpoint='organisationUnits/uid')

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == url


@responses.activate
def test_info():
    url = '{}/system/info.json'.format(API_URL)
    r = {"contextPath": "https://play.dhis2.org/2.29"}

    responses.add(responses.GET, url, json=r, status=200)

    api = Dhis(BASEURL, 'admin', 'district')
    resp = api.info()

    assert resp == json.dumps(r, indent=2)
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == url
    assert responses.calls[0].response.text == json.dumps(r)


@pytest.mark.parametrize("from_server,integer", [
    ("2.29", 29),
    ("2.30", 30),
    ("2.30-SNAPSHOT", 30)
])
@responses.activate
def test_dhis_version(from_server, integer):
    url = '{}/system/info.json'.format(API_URL)
    r = {"version": from_server}

    responses.add(responses.GET, url, json=r, status=200)

    api = Dhis(BASEURL, 'admin', 'district')
    resp = api.dhis_version()

    assert resp == integer
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == url
    assert responses.calls[0].response.text == json.dumps(r)


@responses.activate
def test_dhis_version_invalid():
    url = '{}/system/info.json'.format(API_URL)
    r = {"version": "unknown"}

    responses.add(responses.GET, url, json=r, status=200)

    api = Dhis(BASEURL, 'admin', 'district')
    with pytest.raises(exceptions.ClientException):
        api.dhis_version()


@pytest.mark.parametrize("amount,expected", [
    (100, [100]),
    (10000, [10000]),
    (13000, [10000, 3000]),
    (23000, [10000, 10000, 3000])
])
def test_chunk(amount, expected):
    c = Dhis._chunk(amount)
    assert (set(c) == set(expected))


@responses.activate
def test_generate_uids():
    amount = 13000
    url = '{}/system/id.json'.format(API_URL, amount)

    responses.add_passthru(url)
    api = Dhis(BASEURL, 'admin', 'district')
    uids = api.generate_uids(amount)
    assert (len(uids) == amount)