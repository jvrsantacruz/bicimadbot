# -*- coding: utf-8 -*-
import json
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

    def filter_by(self, filters):
        return (station for station in self.stations
                if all(filter(station) for filter in filters))

    def close_to(self, id, meters=None):
        meters = meters or 500
        return (station for station in self.stations
                if station.id != id and self.distances[id][station.id] <= meters)

    def close_to_position(self, position, meters=None):
        meters = meters or 500
        return (station for station in self.stations
                if station.distance_to_position(position) <= meters)


class Filter(object):
    def __init__(self, name, cmp, value):
        self.name = name
        self.cmp = cmp
        self.value = value
        self.compare = self.operators[cmp]
        self.getter = operator.attrgetter(name)

    names = ('id', 'name', 'position', 'idestacion', 'nombre', 'direccion',
             'numero_estacion', 'latitud', 'longitud', 'activo', 'luz',
             'no_disponible', 'numero_bases', 'bicis_enganchadas',
             'bases_libres', 'procentaje')

    operators = {
        u'<': operator.lt,
        u'<=': operator.le,
        u'>': operator.gt,
        u'>=': operator.ge,
        u'has': operator.contains,
        u'==': operator.eq,
        u'!=': operator.ne,
    }

    def __call__(self, obj):
        return self.compare(type(self.value)(self.getter(obj)), self.value)

    def __repr__(self):
        return u'Filter({},{},{})'.format(self.name, self.cmp, self.value)


@click.group()
@click.version_option()
def cli():
    """BiciMad cli"""


@cli.group()
def station():
    """BidiMad stations"""


def validate_filters(ctx, param, values):
    try:
        return tuple(Filter(value[0], value[1], value[2]) for value in values)
    except (IndexError, ValueError):
        raise click.BadParameter(u'filters should be in format NAME OP VALUE')


@station.command('list')
@click.option('-v', '--verbose', is_flag=True)
@click.option('-l', '--local', is_flag=True)
@click.option('--url', default=DEFAULT_URL, envvar='BICIMAD_URL')
@click.option('--user', envvar='BICIMAD_USER', help='DNI usuario')
@click.option('--auth', envvar='BICIMAD_AUTH', help='login id_auth')
@click.option('--security', envvar='BICIMAD_SECURITY', help='login id_security')
@click.option('-f', '--filter', nargs=3, multiple=True,
              callback=validate_filters, metavar=u'NAME OP VALUE',
              help=u"Filter stations using conditional expressions.\n"
              u"Available names:\n\n {}\n\n"
              u"Available comparators:\n\n {}".format(
                  u', '.join(Filter.names),
                  u', '.join(Filter.operators.keys())))
def stations_list(verbose, local, url, user, auth, security, filter):
    """List and filter stations"""
    if local:
        response = json.load(open('bicimad-response.json'))
    else:
        response = get_locations(url, user, auth, security)

    if not response['success']:
        click.secho(u'Unsuccessful response: {}'.format(response), fg='red')
        return

    collection = Stations.from_response(response)

    if verbose:
        click.secho(u'Using filters: {}'.format(filter), fg='yellow')
    click.echo(u'\n'.join(map(str, collection.filter_by(filter))))
