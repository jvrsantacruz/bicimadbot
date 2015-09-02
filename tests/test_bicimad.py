import json as stdjson

from bicimad.helpers import urljoin
from bicimad.bicimad import BiciMad, DEFAULT_URL, ENDPOINT, Stations, Station

from .stations import (RESPONSE, N_STATIONS, AVAILABLE_STATION,
                       NO_ACTIVE_STATION, UNAVAILABLE_STATION)

import httpretty
from hamcrest import (assert_that, has_property, has_entry, is_, has_entries,
                      has_length, only_contains, greater_than, has_properties,
                      all_of, none, any_of, contains_string)


ID_USER = '74582027C'
ID_AUTH = '203a98b42df039094dfff2043'
ID_SECURITY = '3a98b42df039094dfff2043f039094dfff2043'


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

        assert_that(list(stations.stations), has_length(N_STATIONS))

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


class TestStation:
    def test_it_should_say_its_enabled_when_ok(self):
        assert_that(self.active, has_property('enabled', True))

    def test_it_should_be_not_active_its_no_activo(self):
        assert_that(self.no_active, has_property('enabled', False))

    def test_it_should_be_not_active_its_no_disponible(self):
        assert_that(self.unavailable, has_property('enabled', False))

    def setup(self):
        self.active = Station(AVAILABLE_STATION)
        self.no_active = Station(NO_ACTIVE_STATION)
        self.unavailable = Station(UNAVAILABLE_STATION)


class TestStations:
    def test_it_should_parse_stations(self):
        stations = list(self.stations.stations)

        assert_that(stations, has_length(N_STATIONS))

    def test_it_should_get_closest_bikes(self):
        position = (40.4168984, -3.7024244)
        stations = list(self.stations.by_distance(position))

        assert_that(stations, all_of(
            has_length(greater_than(0)),
            only_contains(has_properties(dict(
                distance=greater_than(0)
            )))
        ))

    def test_it_should_search_stations_with_bikes_by_name(self):
        query = 'callEaVapiés'
        stations = list(self.stations.by_search(query))

        assert_that(stations, only_contains(any_of(
            has_property('nombre', contains_string('Lavapies')),
            has_property('direccion', contains_string('Lavapies')),
        )))
        assert_that(stations, has_length(greater_than(0)))

    def test_it_should_search_stations_with_bikes_by_id(self):
        station = self.stations.by_id(1)

        assert_that(station, has_property('id', 1))

    def test_it_should_give_none_when_station_with_bikes_not_found_by_id(self):
        station = self.stations.by_id(9999)

        assert_that(station, is_(none()))

    def setup(self):
        self.stations = Stations.from_response(RESPONSE)
