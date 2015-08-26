import json

from bicimad.helpers import urljoin
from bicimad.telegram import Telegram

import httpretty
from hamcrest import (assert_that, has_property, all_of, ends_with,
                      starts_with, is_, has_entry, has_entries)


HOST = 'https://api.none.com'
TOKEN = 'ab209e3daffa293'
CHAT_ID = 10943
TEXT = 'communication with the user'


class TestTelegram:
    def test_it_should_set_url(self):
        assert_that(self.telegram, has_property('url',
            all_of(starts_with(HOST), ends_with('bot' + TOKEN))))

    @httpretty.activate
    def test_it_should_get_updates(self):
        self.register('getUpdates')

        updates = self.telegram.get_updates()

        assert_that(updates, is_(self.response))

    @httpretty.activate
    def test_it_should_get_updates_with_offset(self):
        self.register('getUpdates')

        self.telegram.get_updates(1)

        assert_that(httpretty.last_request().querystring,
                    has_entry('offset', ['1']))

    @httpretty.activate
    def test_it_should_send_messages(self):
        self.register('sendMessage')

        self.telegram.send_message(CHAT_ID, TEXT)

        assert_that(httpretty.last_request().querystring,
            has_entries({'chat_id': [str(CHAT_ID)], 'text': [TEXT]}))

    def register(self, endpoint, json_=None):
        httpretty.register_uri(
            httpretty.GET,
            urljoin(self.telegram.url, endpoint),
            body=self.json_response,
            content_type='application/json'
        )

    def setup(self):
        self.telegram = Telegram(HOST, TOKEN)
        self.response = {}
        self.json_response = json.dumps(self.response)
