# -*- coding: utf-8 -*-
import logging
import requests

from .helpers import urljoin


DEFAULT_HOST = 'https://api.telegram.org'

log = logging.getLogger('bicimad.telegram')


def itemgetter(*fields):
    def getter(item):
        return tuple(map(item.get, fields))
    return getter


unpack_message = itemgetter('from', 'chat', 'text', 'location')
unpack_user = itemgetter('first_name', 'last_name', 'id')
unpack_location = itemgetter('latitude', 'longitude')
format_station = '{0.bikes} bicis en {0.direccion} ({0.id})'.format


def repr_user(user):
    return 'User(name="{} {}", id={})'.format(*unpack_user(user))


def process_message(update_id, message, telegram, bicimad):
    user, chat, text, location = unpack_message(message)
    chat_id = chat['id']

    if text:
        if text.startswith('/'):
            command = text.split(' ', 1)[0]
            arguments = text.split(' ', 1)[1:]
            if command == '/start':
                response = "¡Hola! Puedo echarte un cable para encontrar \
                    una bicicleta. Comparte conmigo tu posición y te diré \
                    las que tienes más cerca"

            elif command == '/bici':
                if not arguments or not arguments[0].strip():
                    response = 'No me has dicho por qué buscar. '\
                        'Pon "/bici Sol", por poner un ejemplo, '\
                        'o comparte tu posición, y terminamos antes.'
                else:
                    if to_int(arguments[0]):
                        sid = to_int(arguments[0])
                        station = bicimad.stations\
                            .active_stations_with_bikes_by_id(sid)
                        if station is None:
                            response = 'Mmmm, no hay ninguna estación '\
                                'con id {}. Prueba con el nombre.'.format(sid)
                        else:
                            response = 'La estación con id {} '\
                                'es la que está en {}:\n\n{}'\
                                .format(sid, station.direccion,
                                        format_station(station))
                    else:
                        stations = bicimad.stations\
                            .active_stations_with_bikes_by_name(arguments[0])
                        if not stations:
                            response = 'Uhh no me suena esa dirección para '\
                                'ninguna estación. Afina un poco más.'
                        else:
                            response = 'Pues puede que sea alguna de estas:\n\n'\
                                + '\n'.join(map(format_station, stations))

            elif command == '/help':
                response = 'Puedo ayudarte a encontrar una bici si me '\
                    'preguntas con cariño.\nPuedes buscar una estación '\
                    'en concreto buscando por nombre, por ej: "/bici atocha"\n'\
                    'pero es mucho más rápido darle a "compartir posición" y te'\
                    'diré todas las que tienes alrededor.'

            elif command in ('/plaza', '/estacion'):
                response = "Estos comandos funcionarán próximamente"
            else:
                response = "No reconozco esa orden"

            log.info(u'(update: %d chat: %d) Got command: %s from: %s',
                        update_id, chat_id, text, repr_user(user))
            telegram.send_message(chat_id, response)
            return

        log.info('(update: %d chat: %d) Got message from %s: %s',
                    update_id, chat_id, repr_user(user), text)

    elif location:
        lat, long = unpack_location(location)
        log.info(u'(update: %d chat: %d) Got location from %s: lat: %f long: %f',
                    update_id, chat_id, repr_user(user), lat, long)

        stations = bicimad.stations.nearest_active_stations_with_bikes((lat, long))
        message = ('Las bicis que te pillan más cerca son:\n\n'
                   + '\n'.join(map(format_station, stations)))
        telegram.send_message(chat_id, message)
    else:
        log.info(u'(update: %d chat: %d) Unmanaged message from %s: %s',
                    update_id, chat_id, repr_user(user), message)
        telegram.send_message(chat_id, u'No te pillo')


def process_updates(updates, config, telegram, bicimad):
    log.debug(u'Got updates: {}'.format(updates))
    if not updates.get('ok'):
        log.error(u'Got bad update response: %r',
                  updates.get('description', u'Unknown'))
        return

    last_update = config.get('telegram.offset', 0)
    log.debug('Current update offset: %d', last_update)

    for update in updates['result']:
        update_id = update.get('update_id')
        log.debug('(update: %d) Update offset: %d to %d',
                    update_id, last_update, update_id)
        last_update = update_id + 1

        message = update.get('message')
        if message is None:
            log.error('(update: %d) Expected a message in update, got: %r',
                      update_id, update)
            continue

        process_message(update_id, message, telegram, bicimad)

    log.debug(u'Last offset: %d', last_update)
    config['telegram.offset'] = last_update


def to_int(text):
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


class Telegram(object):
    def __init__(self, host, token, timeout=None, poll_timeout=None):
        self.url = urljoin(host, '/bot' + token)
        #: max time to wait for regular responses
        self.timeout = 5 if timeout is None else timeout
        #: max time to wait to the server to send data (see get_updates)
        self.poll_timeout = 300 if poll_timeout is None else poll_timeout

    @classmethod
    def from_config(cls, config):
        return cls(DEFAULT_HOST, config.get('telegram.token'),
                   timeout=to_int(config.get('telegram.timeout')),
                   poll_timeout=to_int(config.get('telegram.poll_timeout')))

    def send_telegram(self, endpoint, **kwargs):
        """Send generic telegram api requests"""
        return requests.get(urljoin(self.url, endpoint),
                            timeout=self.timeout, params=kwargs).json()

    def get_updates(self, offset=0):
        """Get input updates from the server

        It uses long polling to get the updates from the server without making
        a request every so. Performs a long standing request that will resolve
        either when timeout is out or when the server sends some results.

        The ``.poll_timeout`` variable is used to know how much to wait for
        results before starting a new request.

        :param offset: Identifier of the last processed update
        :returns: Response with 'result' containing list of updates.
        """
        # add some time to local timeout to allow the server to finish
        # gracefully without suddently closing the current connection.
        timeout = (self.timeout, self.poll_timeout + 1)

        # Tell the server what to return and how much to wait
        params = dict(offset=offset, timeout=self.poll_timeout)

        return requests.get(urljoin(self.url, 'getUpdates'),
                            timeout=timeout, params=params).json()

    def send_message(self, chat_id, text):
        return self.send_telegram('sendMessage', chat_id=chat_id, text=text)

    def send_location(self, chat_id, latitude, longitude):
        return self.send_telegram('sendLocation', chat_id=chat_id,
                                  latitude=latitude, longitude=longitude)
