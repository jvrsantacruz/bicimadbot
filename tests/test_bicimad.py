import os
import json as stdjson

from bicimad.helpers import urljoin
from bicimad.bicimad import BiciMad, DEFAULT_URL, ENDPOINT, Stations

import httpretty
from hamcrest import (assert_that, has_property, has_entry, is_, has_entries,
                      has_length, only_contains, greater_than, has_properties,
                      all_of, none, instance_of, contains, less_than)


def load_json(path):
    with open(path, 'r') as stream:
        return stdjson.load(stream)


ID_USER = '74582027C'
ID_AUTH = '203a98b42df039094dfff2043'
ID_SECURITY = '3a98b42df039094dfff2043f039094dfff2043'
HERE = os.path.abspath(os.path.dirname(__file__))
RESPONSE = load_json(os.path.join(HERE, '../examples/bicimad-response.json'))
N_STATIONS = len(RESPONSE['estaciones'])


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


class TestStations:
    def test_it_should_parse_stations(self):
        stations = list(self.stations.stations)

        assert_that(stations, has_length(N_STATIONS))

    def test_it_should_get_closest_bikes(self):
        position = (40.4168984, -3.7024244)
        stations = list(self.stations.with_bikes_by_distance(position))

        assert_that(stations, all_of(
            has_length(greater_than(0)),
            only_contains(has_properties(dict(
                bikes=greater_than(0),
                active=is_(1),
                unavailable=is_(0),
                distance=greater_than(0)
            )))
        ))

    def test_it_should_search_stations_by_name(self):
        name = 'callElaVapié'
        stations = list(self.stations.with_bikes_by_address(name))

        assert_that(stations, all_of(
            has_length(1),
            only_contains(has_properties(dict(
                bikes=greater_than(0),
                active=is_(1),
                unavailable=is_(0),
            )))
        ))

    def test_it_should_search_stations_by_id(self):
        station = self.stations.with_bikes_by_id(1)

        assert_that(station, has_properties(dict(
            id=1,
            bikes=greater_than(0),
            active=is_(1),
            unavailable=is_(0),
        )))

    def test_it_should_give_none_when_station_not_found_by_id(self):
        station = self.stations.with_bikes_by_id(9999)

        assert_that(station, is_(none()))

    def setup(self):
        self.stations = Stations.from_response(RESPONSE)


FIRST_STATION = {
    "idestacion":"1",
    "nombre":"Puerta del Sol A",
    "numero_estacion":"1a",
    "direccion":"Puerta del Sol No 1",
    "latitud":"40.4168961",
    "longitud":"-3.7024255",
    "activo":"1",
    "luz":"2",
    "no_disponible":"0",
    "numero_bases":"24",
    "bicis_enganchadas":"8",
    "bases_libres":"7",
    "porcentaje":29.166666666667
}


AVAILABLE_STATION = {
    "idestacion":"56",
    "nombre":"Pza.  Santa Ana",
    "numero_estacion":"52",
    "direccion":"Plaza Santa Ana No 10",
    "latitud":"40.4144226",
    "longitud":"-3.7007164",
    "activo":"1",
    "luz":"1",
    "no_disponible":"0",
    "numero_bases":"24",
    "bicis_enganchadas":"13",
    "bases_libres":"5",
    "porcentaje":20.833333333333
}


UNAVAILABLE_STATION = {
    "idestacion":"57",
    "nombre":"Pza.  Lavapies",
    "numero_estacion":"53",
    "direccion":"NO OPERATIVA",
    "latitud":"40.4089282",
    "longitud":"-3.7008803",
    "activo":"1",
    "luz":3,
    "no_disponible":"1",
    "numero_bases":"24",
    "bicis_enganchadas":"0",
    "bases_libres":"0",
    "porcentaje":0
}

NO_ACTIVE_STATION = {
    "idestacion":"3",
    "nombre":"Miguel Moya",
    "numero_estacion":"2",
    "direccion":"Miguel Moya No 1",
    "latitud":"40.4205886",
    "longitud":"-3.7058415",
    "activo":"0",
    "luz":"0",
    "no_disponible":"0",
    "numero_bases":"24",
    "bicis_enganchadas":"0",
    "bases_libres":"15",
    "porcentaje":62.5
}

NO_BIKES_STATION = {
    "idestacion":"11",
    "nombre":"Marques de la Ensenada",
    "numero_estacion":"10",
    "direccion":"Calle Marques de la Ensenada No 16",
    "latitud":"40.4250863",
    "longitud":"-3.6918807",
    "activo":"1",
    "luz":"0",
    "no_disponible":"0",
    "numero_bases":"24",
    "bicis_enganchadas":"0",
    "bases_libres":"24",
    "porcentaje":100
}


from bicimad.bicimad import (Station, active, distance, with_bikes, search,
                             find, sort, query)

class FilterTest:
    def filter(self, filter, specs):
        return filter(self.stations(specs))

    def stations(self, specs):
        return map(Station, specs)


class TestActive(FilterTest):
    def test_it_should_filter_unavailable_stations(self):
        result = self.filter(active, (AVAILABLE_STATION, UNAVAILABLE_STATION))

        assert_that(result, only_contains(
            has_property('idestacion', AVAILABLE_STATION['idestacion'])))

    def test_it_should_filter_not_active_stations(self):
        result = self.filter(active, (AVAILABLE_STATION, NO_ACTIVE_STATION))

        assert_that(result, only_contains(
            has_property('idestacion', AVAILABLE_STATION['idestacion'])))


class TestWithBikes(FilterTest):
    def test_it_should_filter_stations_with_no_bikes(self):
        result = self.filter(with_bikes, (AVAILABLE_STATION, NO_BIKES_STATION))

        assert_that(result, only_contains(
            has_property('idestacion', AVAILABLE_STATION['idestacion'])))


class TestDistance(FilterTest):
    def test_it_should_calculate_0_as_distance_to_same_point(self):
        """Check it actually computes distances"""
        position = AVAILABLE_STATION['latitud'], AVAILABLE_STATION['longitud']
        result = self.filter(distance(position),
                             (AVAILABLE_STATION, NO_BIKES_STATION))

        assert_that(result, contains(
            has_property('distance', 0.0),
            has_property('distance', all_of(greater_than(1401), less_than(1402)))
        ))


class TestSearch(FilterTest):
    def test_it_should_search_by_field(self):
        """Searches by given field"""
        result = self.filter(search('direccion', 'Plaza Santa Ana'),
                             (AVAILABLE_STATION, NO_BIKES_STATION))

        assert_that(result, contains(
            has_property('idestacion', AVAILABLE_STATION['idestacion'])))

    def test_it_should_sanitize_search_terms(self):
        """Removes street terms from search terms"""
        result = self.filter(search('direccion', 'Calle Santa Ana'),
                             (AVAILABLE_STATION, NO_BIKES_STATION))

        assert_that(result, contains(
            has_property('idestacion', AVAILABLE_STATION['idestacion'])))


class TestFind(FilterTest):
    def test_it_should_find_by_field(self):
        """Should return a station with given spec"""
        result = self.filter(find('id', int(AVAILABLE_STATION['idestacion'])),
                             (AVAILABLE_STATION, NO_BIKES_STATION))

        assert_that(result, is_(
            has_property('idestacion', AVAILABLE_STATION['idestacion'])))

    def test_it_should_return_none_when_not_found(self):
        result = self.filter(find('id', 0), (AVAILABLE_STATION, NO_BIKES_STATION))

        assert_that(result, is_(none()))


class TestSort(FilterTest):
    def test_it_should_sort_by_field(self):
        result = self.filter(sort('id'), (AVAILABLE_STATION, FIRST_STATION))

        assert_that(result, contains(
            has_property('idestacion', FIRST_STATION['idestacion']),
            has_property('idestacion', AVAILABLE_STATION['idestacion'])
        ))


class TestQuery(FilterTest):
    def test_it_should_compose_several_filters_in_order(self):
        """Should apply all filters in order and keep the result"""
        def marker(n):
            def filter(stations):
                for station in stations:
                    setattr(station, 'mark', n)
                    setattr(station, 'marked_by_{}'.format(n), True)
                    yield station
            return filter

        result = self.filter(query(marker(1), marker(2)),
                             (AVAILABLE_STATION, FIRST_STATION))

        assert_that(result, only_contains(all_of(
            has_property('mark', 2),
            has_property('marked_by_1', True),
            has_property('marked_by_2', True),
        )))
