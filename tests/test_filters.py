from .stations import (AVAILABLE_STATION, FIRST_STATION, UNAVAILABLE_STATION,
                       NO_ACTIVE_STATION, NO_BIKES_STATION, NO_SPACES_STATION,
                       NAME_AND_ADDRESS_STATION)

from hamcrest import (assert_that, has_property, is_, only_contains,
                      greater_than, all_of, none, contains, less_than,
                      contains_string)

from bicimad.bicimad import (Station, enabled, distance, with_bikes, search,
                             find, sort, query, index, with_spaces)


class FilterTest:
    def filter(self, filter, specs):
        return filter(self.stations(specs))

    def stations(self, specs):
        return map(Station, specs)


class TestEnabled(FilterTest):
    def test_it_should_filter_unavailable_stations(self):
        result = self.filter(enabled, (AVAILABLE_STATION, UNAVAILABLE_STATION))

        assert_that(result, only_contains(
            has_property('idestacion', AVAILABLE_STATION['idestacion'])))

    def test_it_should_filter_not_enabled_stations(self):
        result = self.filter(enabled, (AVAILABLE_STATION, NO_ACTIVE_STATION))

        assert_that(result, only_contains(
            has_property('idestacion', AVAILABLE_STATION['idestacion'])))


class TestWithBikes(FilterTest):
    def test_it_should_filter_stations_with_no_bikes(self):
        result = self.filter(with_bikes, (AVAILABLE_STATION, NO_BIKES_STATION))

        assert_that(result, only_contains(
            has_property('idestacion', AVAILABLE_STATION['idestacion'])))


class TestWithSpaces(FilterTest):
    def test_it_should_filter_stations_with_no_spaces(self):
        result = self.filter(with_spaces, (AVAILABLE_STATION, NO_SPACES_STATION))

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
        filter = query(index('direccion'), search('Plaza Santa Ana'))

        result = self.filter(filter, (AVAILABLE_STATION, NO_BIKES_STATION))

        assert_that(result, contains(
            has_property('idestacion', AVAILABLE_STATION['idestacion'])))

    def test_it_should_sanitize_search_terms(self):
        """Removes street terms from search terms"""
        filter = query(index('direccion'), search('Plaza Santa Ana'))

        result = self.filter(filter, (AVAILABLE_STATION, NO_BIKES_STATION))

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


class TestIndex(FilterTest):
    def test_it_should_create_a_index_property(self):
        result = self.filter(index('nombre', 'direccion'),
                            (FIRST_STATION, AVAILABLE_STATION))

        assert_that(result, only_contains(has_property('index')))

    def test_it_should_create_an_index_using_station_data(self):
        result = self.filter(index('nombre', 'direccion'),
                            (NAME_AND_ADDRESS_STATION,))

        assert_that(result, contains(has_property('index', all_of(
            contains_string('matadero'),
            contains_string('chopera'))
        )))
