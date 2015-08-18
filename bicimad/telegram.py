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
format_station = '{0.bikes} | ({0.id}) {0.direccion}'.format


def repr_user(user):
    return 'User(name="{} {}", id={})'.format(*unpack_user(user))


def process_message(update_id, message, telegram, bicimad):
    user, chat, text, location = unpack_message(message)
    chat_id = chat['id']

    if text:
        if text.startswith('/'):
            command = text.split()
            if command[0] in ('/bici', '/plaza', '/estacion'):
                log.info(u'(update: %d chat: %d) Got command: %s from: %s',
                            update_id, chat_id, text, repr_user(user))
                telegram.send_message(chat_id, u'¡Susordenes!')
                return

        log.info('(update: %d chat: %d) Got message from %s: %s',
                    update_id, chat_id, repr_user(user), text)

    elif location:
        lat, long = unpack_location(location)
        log.info(u'(update: %d chat: %d) Got location from %s: lat: %f long: %f',
                    update_id, chat_id, repr_user(user), lat, long)

        stations = bicimad.stations.nearest_active_stations_with_bikes((lat, long))
        telegram.send_message(chat_id, 'Estaciones con bicis que mejor te pillan:\n\n'
                            + '\n'.join(map(format_station, stations)))
    else:
        log.info(u'(update: %d chat: %d) Unmanaged message from %s: %s',
                    update_id, chat_id, repr_user(user), message)
        telegram.send_message(chat_id, u'No te pillo')


def process_updates(updates, context, telegram, bicimad):
    log.debug(u'Got updates: {}'.format(updates))
    if not updates.get('ok'):
        log.error(u'Got bad update response: %r',
                  updates.get('description', u'Unknown'))
        return

    last_update = context.get('offset', 0)
    log.debug('Current update offset: %d', last_update)

    for update in updates['result']:
        update_id = update.get('update_id')
        if update_id > last_update:
            log.debug('(update: %d) Update offset: %d to %d',
                      update_id, last_update, update_id)
            last_update = update_id

        message = update.get('message')
        if message is None:
            log.error('(update: %d) Expected a message in update, got: %r',
                      update_id, update)
            continue

        process_message(update_id, message, telegram, bicimad)

    log.debug(u'Last offset: %d', last_update)


class Telegram(object):
    def __init__(self, host, token):
        self.url = urljoin(host, '/bot' + token)

    @classmethod
    def from_config(cls, config):
        return cls(DEFAULT_HOST, config.get('telegram.token'))

    def send_telegram(self, endpoint, **kwargs):
        return requests.get(urljoin(self.url, endpoint), params=kwargs).json()

    def get_updates(self, offset=0):
        return self.send_telegram('getUpdates', offset=offset)

    def send_message(self, chat_id, text):
        return self.send_telegram('sendMessage', chat_id=chat_id, text=text)

    def send_location(self, chat_id, latitude, longitude):
        return self.send_telegram('sendLocation', chat_id=chat_id,
                                  latitude=latitude, longitude=longitude)
