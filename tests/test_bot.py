# -*- coding: utf-8 -*-

from bicimad.telegram import Telegram
from bicimad.bot import process_message
from bicimad.bicimad import BiciMad, Stations

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
    Obj(id=100, enabled=True, bikes=0, spaces=0, address='C/ Dirección A'),
    Obj(id=101, enabled=True, bikes=1, spaces=1, address='C/ Dirección B'),
]

BAD_STATIONS = [
    Obj(id=200, enabled=False, bikes=0, spaces=0, address='C/ Dirección W'),
    Obj(id=201, enabled=False, bikes=1, spaces=1, address='C/ Dirección X'),
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


class SearchCommand(ProcessMessage):
    command = ''
    queryname = ''

    def set_result(self, all, good=[]):
        self.bicimad.stations.by_search.return_value = all
        function = getattr(self.bicimad.stations, self.queryname)
        function.return_value = good

    def process_with_args(self, argument):
        self.process(message('/{} {}'.format(self.command, argument)))

    def test_it_should_check_arguments(self):
        self.process_with_args('  \n')

        self.assert_answer(contains_string('No me has dicho'))

    def test_it_should_answer_with_no_results_message(self):
        self.set_result([])

        self.process_with_args('wwwwww')

        self.assert_answer(contains_string('no me suena'))

    def test_it_should_answer_only_with_good_results(self):
        self.set_result(STATIONS, STATIONS)

        self.process_with_args('wwwwww')

        self.assert_answer(all_of(
            contains_string('puede que sea alguna de estas'),
            contains_string(self.command),
            contains_string(STATIONS[0].address),
            contains_string(STATIONS[1].address)
        ))

    def test_it_should_answer_with_good_and_bad_results(self):
        self.set_result(STATIONS + BAD_STATIONS, STATIONS)

        self.process_with_args('wwwwww')

        self.assert_answer(all_of(
            contains_string('puede que sea alguna de estas'),
            contains_string('Estas me salen pero no creo que te sirvan'),
            contains_string(self.command),
            contains_string(STATIONS[0].address),
            contains_string(STATIONS[1].address),
            contains_string(BAD_STATIONS[0].address),
            contains_string(BAD_STATIONS[1].address)
        ))

    def test_it_should_answer_only_with_bad_results(self):
        self.set_result(BAD_STATIONS, [])

        self.process_with_args('wwwwww')

        self.assert_answer(all_of(
            contains_string('Estas me salen pero no creo que te sirvan'),
            contains_string(BAD_STATIONS[0].address),
            contains_string(BAD_STATIONS[1].address)
        ))

    def test_it_should_answer_searching_by_id(self):
        self.bicimad.stations.by_id.return_value = STATIONS[0]

        self.process_with_args('  1')

        self.assert_answer(contains_string(STATIONS[0].address))

    def test_it_should_answer_by_id_with_no_results_message(self):
        self.bicimad.stations.by_id.return_value = None

        self.process_with_args('  9999')

        self.assert_answer(contains_string('ninguna estación'))


class TestBiciCommand(SearchCommand):
    command = 'bici'
    queryname = 'with_bikes'


class TestPlazaCommand(SearchCommand):
    command = 'plaza'
    queryname = 'with_spaces'


class TestEstacionCommand(ProcessMessage):
    def test_it_should_process_estacion_command(self):
        self.process(message('/estacion'))

        self.assert_answer(self.command_not_implemented)

    command_not_implemented = contains_string(
        'Este comando funcionará próximamente')


class TestProcessLocation(ProcessMessage):
    def test_it_should_query_available_bikes(self):
        self.process(MSG_LOCATION)

        self.bicimad.stations.by_distance.assert_called_once_with(LOCATION)

    def test_it_should_answer_message(self):
        self.process(MSG_LOCATION)

        self.assert_answer(all_of(
            contains_string('ninguna bici y ninguna plaza en '
                            'C/ Dirección A (100) a 100 metros'),
            contains_string('1 bici y 1 plaza en '
                            'C/ Dirección B (101) a 100 metros')
        ))

    def stations(self):
        for station in STATIONS:
            station.distance = 100.05
            yield station

    def setup(self):
        self.setup_mocks()
        self.bicimad.stations.by_distance.return_value = list(self.stations())
