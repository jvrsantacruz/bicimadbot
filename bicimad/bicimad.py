# -*- coding: utf-8 -*-
import re
import operator
import unidecode

import requests
from geopy.distance import vincenty

from .helpers import urljoin


DEFAULT_HOST = u'helena.bonopark.es:16080'
DEFAULT_URL = u'http://' + DEFAULT_HOST
ENDPOINT = u'/app/app/functions/get_all_estaciones_new.php'


def geo_distance(pos1, pos2):
    """Distance between two points (lat, long) in meters"""
    return vincenty(pos1, pos2).m


def get_locations(base_url, dni, id_auth, id_security):
    url = urljoin(base_url, ENDPOINT)
    headers = {u'User-Agent': u'Apache-HttpClient/UNAVAILABLE (java 1.4)'}
    data = dict(dni=dni, id_auth=id_auth, id_security=id_security)
    return requests.post(url, json=data, headers=headers).json()


class Station:
    def __init__(self, data):
        """Station from response item

    {
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
      "bicis_enganchadas":"8"e
      "bases_libres":"7",
      "porcentaje":29.166666666667
    }

        """
        for key, value in data.items():
            setattr(self, key, value)

        self.id = int(self.idestacion)
        self.spaces = int(self.bases_libres)
        self.bikes = int(self.bicis_enganchadas)
        self.enabled = bool(int(self.activo) and not int(self.no_disponible))
        self.position = float(self.latitud), float(self.longitud)
        self.address = self.direccion if \
            self.direccion != 'NO OPERATIVA' else self.nombre

    def distance_to(self, position):
        return geo_distance(self.position, position)

    def __str__(self):
        return '{} ({})'.format(self.address, self.id)

    def __repr__(self):
        return str(self)


def enabled(stations):
    """Active and not unavailable stations"""
    return (s for s in stations if s.enabled)


def with_bikes(stations):
    """With available bikes"""
    return (s for s in stations if s.bikes)


def with_spaces(stations):
    """With free spaces"""
    return (s for s in stations if s.spaces)


def distance(position):
    """Ordered by distance to a point

    Adds a `distance` property to each station relative to `position`.

    :param position: (lat, long)
    """
    def calculate_distances(stations):
        for station in stations:
            station.distance = station.distance_to(position)
            yield station

    return calculate_distances


def make_getter(*fields):
    """Build getter that always returns a tuple of values

    operator.attrgetter returns the value with one field instead of a tuple.
    """
    getter = operator.attrgetter(*fields)

    # assure always returns a tuple
    if len(fields) == 1:
        def single_getter(value):
            return (getter(value),)
        return single_getter

    return getter


def index(*fields):
    """Indexes station fields for latter search

    Adds a `index` property to each station with resumed search data.

    :param \*fields: Field names to add to the index
    """
    def indexer(stations):
        getter = make_getter(*fields)
        for station in stations:
            station.index = normalize(' '.join(getter(station)))
            yield station

    return indexer


def search(value):
    """Search by name/address field

    Expects a `index` property with a normalized search string.
    Filters stations matching the search value.
    """
    def search(stations):
        query = normalize(value)
        for station in stations:
            if query in station.index:
                yield station

    return search


def find(field, value):
    """Find one by the exact value or return None"""
    def filter(stations):
        for station in stations:
            if getattr(station, field) == value:
                return station

    return filter


def sort(field):
    def filter(stations):
        return sorted(stations, key=operator.attrgetter(field))
    return filter


def query(*filters):
    def filter_all(stations):
        for filter in filters:
            stations = filter(stations)
        return stations

    return filter_all


class Stations:
    def __init__(self, stations):
        self.stations = map(Station, stations)

    @classmethod
    def from_response(cls, response):
        return cls(response['estaciones'])

    def query(self, *filters, **kwargs):
        max = kwargs.get('max')
        stations = kwargs.get('stations', self.stations)
        result = query(*filters)(stations)
        return list(result)[:max] if max is not None else result

    def by_id(self, id):
        return self.query(find('id', id))

    def by_search(self, query, max=5):
        return self.query(index('nombre', 'address'),
                          search(query), sort('index'), max=max)

    def by_distance(self, position, max=5):
        return self.query(distance(position), sort('distance'), max=max)

    def with_bikes(self, stations, max=5):
        return self.query(enabled, with_bikes, stations=stations, max=max)

    def with_spaces(self, stations, max=5):
        return self.query(enabled, with_spaces, stations=stations, max=max)

    def with_some_use(self, stations, max=5):
        return self.query(enabled, with_spaces,
                          with_bikes, stations=stations, max=max)


def normalize(name):
    """Normalize spanish addresses for searching"""
    return _NORMALIZE_RE.sub('', unidecode.unidecode(name).lower()).strip()


# Normalize spanish addresses
_NORMALIZE_RE = re.compile(r"""
(plaza)         # plazas y plazuelas
|(plazuela)
|(calle)        # calles y avenidas
|(c/)
|(av/)
|(avda\.)
|(\ no\ \d+)    # números
|(\d+)
|([-,()])       # caracteres especiales
""", re.VERBOSE)


class BiciMad:
    def __init__(self, url, user, auth, security):
        self.url = url
        self.user = user
        self.auth = auth
        self.security = security

    @classmethod
    def from_config(cls, config):
        return cls(DEFAULT_URL,
                   config.get('bicimad.user'),
                   config.get('bicimad.auth'),
                   config.get('bicimad.security'))

    @property
    def stations(self):
        return Stations.from_response(self.get_locations())

    def get_locations(self):
        return get_locations(self.url, self.user, self.auth, self.security)
