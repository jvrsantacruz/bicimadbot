# -*- coding: utf-8 -*-
import operator

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
        self.bikes = int(self.bicis_enganchadas)
        self.active = int(self.activo)
        self.unavailable = int(self.no_disponible)
        self.position = float(self.latitud), float(self.longitud)

    def distance_to(self, position):
        return geo_distance(self.position, position)


class Stations:
    def __init__(self, stations):
        self.stations = map(Station, stations)

    @classmethod
    def from_response(cls, response):
        return cls(response['estaciones'])

    @property
    def active_stations(self):
        return (s for s in self.stations if s.active and not s.unavailable)

    @property
    def active_stations_with_bikes(self):
        return (s for s in self.active_stations if s.bikes)

    def calculate_distances(self, stations, position):
        for station in stations:
            station.distance = station.distance_to(position)
            yield station

    def nearest_active_stations_with_bikes(self, position, max=5):
        stations = self.active_stations_with_bikes
        stations = self.calculate_distances(stations, position)
        return sorted(stations, key=operator.attrgetter('distance'))[:max]


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
