import json
import datetime

from bicimad.helpers import urljoin
from bicimad.telegram import Telegram, Update

import httpretty
from hamcrest import (assert_that, has_property, all_of, ends_with,
                      starts_with, is_, has_entry, has_entries, has_properties)

from .messages import UPDATE_CHAT, UPDATE_COMMAND, UPDATE_LOCATION, LOCATION


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

        assert_that(self.sent_json, has_entry('offset', 1))

    @httpretty.activate
    def test_it_should_send_messages(self):
        self.register('sendMessage')

        self.telegram.send_message(CHAT_ID, TEXT)

        assert_that(self.sent_json,
            has_entries({'chat_id': CHAT_ID, 'text': TEXT}))

    @httpretty.activate
    def test_it_should_force_reply(self):
        self.register('sendMessage')

        self.telegram.send_message(CHAT_ID, TEXT, force_reply=True)

        assert_that(self.sent_json,
            has_entry('reply_markup', has_entry('force_reply', True)))

    @httpretty.activate
    def test_it_should_set_selective(self):
        self.register('sendMessage')

        self.telegram.send_message(CHAT_ID, TEXT, selective=True)

        assert_that(self.sent_json, has_entry('selective', True))

    @property
    def sent_json(self):
        return json.loads(httpretty.last_request().body.decode('utf-8'))

    def register(self, endpoint, json_=None):
        httpretty.register_uri(
            httpretty.POST,
            urljoin(self.telegram.url, endpoint),
            body=self.json_response,
            content_type='application/json'
        )

    def setup(self):
        self.telegram = Telegram(HOST, TOKEN)
        self.response = {}
        self.json_response = json.dumps(self.response)


class UpdateTest:
    type = None
    response = None

    def test_it_should_have_update_id(self):
        assert_that(self.update, has_property(
            'id', self.response.get('update_id')))

    def test_it_should_have_message_id(self):
        assert_that(self.update, has_property(
            'message_id', self.response['message']['message_id']))

    def test_it_should_have_sender(self):
        assert_that(self.update, has_property(
            'sender', has_properties(self.response['message']['from'])))

    def test_it_should_have_chat(self):
        assert_that(self.update, has_property(
            'chat', is_(self.response['message']['chat'])))

    def test_it_should_have_chat_id(self):
        assert_that(self.update, has_property(
            'chat_id', self.response['message']['chat']['id']))

    def test_it_should_have_date(self):
        assert_that(self.update, has_property('date', is_(
            datetime.datetime.fromtimestamp(self.response['message']['date']))))

    def test_it_should_have_text_type_when_is_text(self):
        assert_that(self.update, has_property('type', is_(self.type)))

    def setup(self):
        self.update = Update.from_response(self.response)


class TestTextUpdate(UpdateTest):
    type = 'text'
    response = UPDATE_CHAT

    def test_it_should_have_text(self):
        assert_that(self.update, has_property(
            'text', is_(self.response['message']['text'])))


class TestCommandUpdate(UpdateTest):
    type = 'command'
    response = UPDATE_COMMAND

    def test_it_should_have_text(self):
        assert_that(self.update, has_property(
            'text', is_(self.response['message']['text'])))

    def test_it_should_have_command(self):
        assert_that(self.update, has_property('command', is_('bici')))

    def test_it_should_have_arguments(self):
        assert_that(self.update, has_property('arguments', 'arg1 arg2'))


class TestLocationUpdate(UpdateTest):
    type = 'location'
    response = UPDATE_LOCATION

    def test_it_should_have_location(self):
        assert_that(self.update, has_property('location', is_(LOCATION)))
