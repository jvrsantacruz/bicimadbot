import os
import json as stdjson

from bicimad.helpers import urljoin
from bicimad.bicimad import BiciMad, DEFAULT_URL, ENDPOINT

import httpretty
from hamcrest import (assert_that, has_property, has_entry, is_, has_entries,
                      has_length)


def load_json(path):
    with open(path, 'r') as stream:
        return stdjson.load(stream)


ID_USER = '74582027C'
ID_AUTH = '203a98b42df039094dfff2043'
ID_SECURITY = '3a98b42df039094dfff2043f039094dfff2043'
HERE = os.path.abspath(os.path.dirname(__file__))
RESPONSE = load_json(os.path.join(HERE, '../examples/bicimad-response.json'))


class TestBiciMad:

    @httpretty.activate
    def test_it_should_get_locations(self):
        self.register(RESPONSE)

        response = self.bicimad.get_locations()

        assert_that(response, is_(RESPONSE))

    @httpretty.activate
    def test_it_should_mock_android_client(self):
        self.register(RESPONSE)

        self.bicimad.get_locations()

        assert_that(httpretty.last_request(), has_property('headers',
            has_entry('User-Agent', u'Apache-HttpClient/UNAVAILABLE (java 1.4)')))

    @httpretty.activate
    def test_it_should_send_auth_params(self):
        self.register(RESPONSE)

        self.bicimad.get_locations()

        assert_that(httpretty.last_request(), has_property('parsed_body',
            has_entries(dict(dni=ID_USER, id_auth=ID_AUTH, id_security=ID_SECURITY))))

    @httpretty.activate
    def test_it_should_get_stations(self):
        self.register(RESPONSE)

        stations = self.bicimad.stations

        assert_that(list(stations.stations),
                    has_length(len(RESPONSE['estaciones'])))

    def register(self, json):
        httpretty.register_uri(
            httpretty.POST,
            urljoin(DEFAULT_URL, ENDPOINT),
            body=stdjson.dumps(json),
            content_type='application/json'
        )

    def setup(self):
        self.bicimad = BiciMad.from_config({
            'bicimad.user': ID_USER,
            'bicimad.auth': ID_AUTH,
            'bicimad.security': ID_SECURITY
        })
