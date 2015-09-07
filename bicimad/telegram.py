import logging
import datetime
import requests

from .bot import process_message
from .helpers import urljoin, to_int


DEFAULT_HOST = 'https://api.telegram.org'

log = logging.getLogger('bicimad.telegram')


def process_updates(updates, config, telegram, bicimad):
    log.debug(u'Got updates: {}'.format(updates))
    if not updates.get('ok'):
        log.error(u'Got bad update response: %r',
                  updates.get('description', u'Unknown'))
        return

    last_update = config.get('telegram.offset', 0)
    log.debug('Current update offset: %d', last_update)

    for update in map(Update.from_response, updates['result']):
        log.debug('(update: %d) Update offset: %d to %d',
                    update.id, last_update, update.id)
        last_update = update.id + 1

        if update.message is None:
            log.error('(update: %d) Expected a message in update, got: %r',
                      update.id, update.raw)
            continue

        process_message(update, telegram, bicimad)

    log.debug(u'Last offset: %d', last_update)
    config['telegram.offset'] = last_update


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


class Update:
    def __init__(self, update):
        """Load from Telegram Update

    {
      "update_id": 987235638,
      "message": {
        "message_id": 25,
        "from": {
          "id": 4128581,
          "first_name": "Javier",
          "last_name": "Santacruz"
        },
        "chat": {
          "id": 4128581,
          "first_name": "Javier",
          "last_name": "Santacruz"
        },
        "date": 1439860509,
        "text": "/bici"
      }
    }
        """
        self.raw = update
        self.id = update['update_id']
        self.message = update['message']
        self.message_id = self.message['message_id']
        self.sender = self.message['from']
        self.chat = self.message['chat']
        self.chat_id = self.chat['id']
        self.date = datetime.datetime.fromtimestamp(self.message.get('date'))

    @classmethod
    def from_response(cls, update):
        """Create update from a Telegram response Update

        Factory method that will return a instance of the most appropiate
        Update type for the given update input.

        :param update: `from_dict` method
        :returns: Update subtype instance
        """
        for subcls in cls.__subclasses__():
            if subcls.accepts(update):
                return subcls(update)


class TextUpdate(Update):
    type = 'text'

    def __init__(self, data):
        super().__init__(data)
        self.text = self.message['text']

    @staticmethod
    def accepts(update):
        text = update['message'].get('text')
        return text is not None and not is_command(text)


class CommandUpdate(Update):
    type = 'command'

    def __init__(self, data):
        super().__init__(data)
        self.text = self.message['text']
        self.command, self.arguments = self.parse_command(self.text)

    @staticmethod
    def accepts(update):
        text = update['message'].get('text')
        return text and is_command(text)

    def parse_command(self, text):
        parsed = text.split(' ', 1)
        command = parsed[0].strip('/')
        arguments = ' '.join(parsed[1:]).strip()
        return command, arguments


class LocationUpdate(Update):
    type = 'location'

    def __init__(self, data):
        super().__init__(data)
        self.location = (self.message['location']['latitude'],
                         self.message['location']['longitude'])

    @staticmethod
    def accepts(update):
        return 'location' in update['message']


def is_command(text):
    return text.startswith('/')
