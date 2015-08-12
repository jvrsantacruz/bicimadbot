# -*- coding: utf-8 -*-
import operator
from collections import defaultdict

import click
import requests
from geopy.distance import vincenty


DEFAULT_HOST = u'helena.bonopark.es:16080'
DEFAULT_URL = u'http://' + DEFAULT_HOST
ENDPOINT = u'/app/app/functions/get_all_estaciones_new.php'


def urljoin(*fragments):
    return u'/'.join(f.strip(u'/') for f in fragments)


def get_locations(base_url, dni, id_auth, id_security):
    url = urljoin(base_url, ENDPOINT)
    headers = {u'User-Agent': u'Apache-HttpClient/UNAVAILABLE (java 1.4)'}
    data = dict(dni=dni, id_auth=id_auth, id_security=id_security)
    return requests.post(url, json=data, headers=headers).json()


def geo_distance(pos1, pos2):
    return vincenty(pos1, pos2).m


class Station(object):
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
        self.name = self.nombre
        self.ocupation = float(self.porcentaje)

    @property
    def position(self):
        return self.latitud, self.longitud

    def distance_to(self, station):
        return self.distance_to_position(station.position)

    def distance_to_position(self, position):
        return geo_distance(self.position, position)

    def __repr__(self):
        return 'Station(id={}, name={})'.format(self.id, self.name)


class Stations(object):
    def __init__(self, stations):
        self.stations = list(map(Station, stations))
        self.distances = self.compute_distances(self.stations)
        self.station_index = {station.id: station for station in self.stations}

    @classmethod
    def from_response(cls, response):
        return cls(response['estaciones'])

    def compute_distances(self, stations):
        dists = defaultdict(dict)

        for n, orig in enumerate(stations):
            for dest in stations[n + 1:]:
                dists[orig.id][dest.id] = dists[dest.id][dest.id] =\
                    orig.distance_to(dest)

        return dists

    def filter_by(self, close_to=None, close_to_position=None, meters=None, **kwargs):
        stations = self.stations

        if close_to:
            stations = self.close_to(close_to, meters)
        elif close_to_position:
            stations = self.close_to_position(close_to_position, meters)

        for attribute, value in kwargs.items():
            cmp = operator.eq if isinstance(value, float) else operator.contains
            stations = filter_by(stations, attribute, value, cmp)

        return stations

    def close_to(self, id, meters=None):
        meters = meters or 500
        return (station for station in self.stations
                if station.id != id and self.distances[id][station.id] <= meters)

    def close_to_position(self, position, meters=None):
        meters = meters or 500
        return (station for station in self.stations
                if station.distance_to_position(position) <= meters)


def filter_by(stations, attribute, value, cmp):
    getter = operator.attrgetter(attribute)
    return (station for station in stations if cmp(getter(station), value))


@click.group()
def cli():
    """BiciMad cli"""


@cli.group()
def stations():
    """BidiMad stations"""


CMPS = {
    '<': operator.lt,
    '<=': operator.lte,
    '>': operator.gt,
    '>=': operator.gte,
    'has': operator.contains,
    '==': operator.eq,
    '!=': operator.neq,
}


def validate_filters(ctx, param, value):
    if value:
        return param.name, CMPS[value[0]], value[1]


def filter(*args, **kwargs):
    kwargs['nargs'] = 2
    kwargs['callback'] = validate_filters
    return click.option(*args, **kwargs)


@stations.command('list')
@filter('--id')
@filter('--close-to')
@filter('--meters')
@filter('--activo')
@filter('--percentaje')
@filter('--bases_libres')
@filter('--bicis_enganchadas')
def stations_list(**kwargs):
    import json
    response = json.load(open('bicimad-response.json'))
    collection = Stations.from_response(response)
    click.echo(u'\n'.join(collection.filter_by(**kwargs)))
