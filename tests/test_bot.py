# -*- coding: utf-8 -*-

from bicimad.bicimad import BiciMad, Stations
from bicimad.telegram import Telegram, process_message

from unittest.mock import Mock
from hamcrest import assert_that, contains_string, all_of, contains


CHAT_ID = 4128581
UPDATE_ID = 987235637
LOCATION = 40.405742, -3.694103
MSG_LOCATION = {
    "message_id": 21,
    "from": {
        "id": 4128581,
        "first_name": "Javier",
        "last_name": "Santacruz"
    },
    "chat": {
        "id": CHAT_ID,
        "first_name": "Javier",
        "last_name": "Santacruz"
    },
    "date": 1439843938,
    "location": {
        "longitude": -3.694103,
        "latitude": 40.405742
    }
}


def message(text):
    return {
        "message_id": 26,
        "from": {
            "id": 4128581,
            "first_name": "Javier",
            "last_name": "Santacruz"
        },
        "chat": {
            "id": CHAT_ID,
            "first_name": "Javier",
            "last_name": "Santacruz"
        },
        "date": 1439860519,
        "text": text
    }


class Obj:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

STATIONS = [
    Obj(id=100, bikes=0, direccion='C/ Dirección A'),
    Obj(id=101, bikes=1, direccion='C/ Dirección B'),
]


class ProcessMessage:
    def process(self, msg):
        process_message(UPDATE_ID, msg, self.telegram, self.bicimad)

    def setup(self):
        self.setup_mocks()

    def setup_mocks(self):
        self.bicimad = Mock(BiciMad)
        self.bicimad.stations = Mock(Stations)
        self.telegram = Mock(Telegram)

    def assert_answer(self, matcher):
        assert_that(self.telegram.send_message.call_args[0],
                    contains(CHAT_ID, matcher))


class TestStartCommand(ProcessMessage):
    """/start command"""
    def test_it_should_process_start_command(self):
        self.process(message('/start'))

        self.assert_answer(contains_string('¡Hola!'))


class TestHelpCommand(ProcessMessage):
    """/help command"""
    def test_it_should_process_help_command(self):
        self.process(message('/help'))

        self.assert_answer(contains_string('Puedo ayudarte a encontrar una bici'))


class TestBiciCommand(ProcessMessage):
    def test_it_should_check_arguments(self):
        self.process(message('/bici  \n'))

        self.assert_answer(contains_string('No me has dicho'))

    def test_it_should_answer_with_no_results_message(self):
        self.bicimad.stations.with_bikes_by_search.return_value = []

        self.process(message('/bici  wwww'))

        self.assert_answer(contains_string('no me suena'))

    def test_it_should_answer_with_results(self):
        self.bicimad.stations.with_bikes_by_search.return_value = STATIONS

        self.process(message('/bici  wwww'))

        self.assert_answer(all_of(
            contains_string('puede que sea alguna de estas'),
            contains_string(STATIONS[0].direccion),
            contains_string(STATIONS[1].direccion)
        ))

    def test_it_should_answer_searching_by_id(self):
        self.bicimad.stations.with_bikes_by_id.return_value = STATIONS[0]

        self.process(message('/bici  1'))

        self.assert_answer(contains_string(STATIONS[0].direccion))

    def test_it_should_answer_by_id_with_no_results_message(self):
        self.bicimad.stations.with_bikes_by_id.return_value = None

        self.process(message('/bici  9999'))

        self.assert_answer(contains_string('ninguna estación'))


class TestPlazaCommand(ProcessMessage):
    def test_it_should_check_arguments(self):
        self.process(message('/plaza \n'))

        self.assert_answer(contains_string('No me has dicho'))

    def test_it_should_answer_with_no_results_message(self):
        self.bicimad.stations.with_spaces_by_search.return_value = []

        self.process(message('/plaza  wwww'))

        self.assert_answer(contains_string('no me suena'))

    def test_it_should_answer_with_results(self):
        self.bicimad.stations.with_spaces_by_search.return_value = STATIONS

        self.process(message('/plaza  wwww'))

        self.assert_answer(all_of(
            contains_string('puede que sea alguna de estas'),
            contains_string(STATIONS[0].direccion),
            contains_string(STATIONS[1].direccion)
        ))

    def test_it_should_answer_searching_by_id(self):
        self.bicimad.stations.with_spaces_by_id.return_value = STATIONS[0]

        self.process(message('/plaza  1'))

        self.assert_answer(contains_string(STATIONS[0].direccion))

    def test_it_should_answer_by_id_with_no_results_message(self):
        self.bicimad.stations.with_spaces_by_id.return_value = None

        self.process(message('/plaza  9999'))

        self.assert_answer(contains_string('ninguna estación'))


class TestEstacionCommand(ProcessMessage):
    def test_it_should_process_estacion_command(self):
        self.process(message('/estacion'))

        self.assert_answer(self.command_not_implemented)

    command_not_implemented = contains_string(
        'Estos comandos funcionarán próximamente')


class TestProcessLocation(ProcessMessage):
    def test_it_should_query_available_bikes(self):
        self.process(MSG_LOCATION)

        self.bicimad.stations.\
            with_bikes_by_distance.\
            assert_called_once_with(LOCATION)

    def test_it_should_answer_with_bikes_message(self):
        self.process(MSG_LOCATION)

        self.assert_answer(all_of(
            contains_string('0 bicis en C/ Dirección A (100)'),
            contains_string('1 bicis en C/ Dirección B (101)')
        ))

    def setup(self):
        self.setup_mocks()
        self.bicimad.stations\
            .with_bikes_by_distance\
            .return_value = STATIONS
