import logging
import functools


log = logging.getLogger('bicimad.telegram')


unpack_user = itemgetter('first_name', 'last_name', 'id')
unpack_location = itemgetter('latitude', 'longitude')
def coroutine(function):
    """Coroutine decorator"""
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        routine = function(*args, **kwargs)
        next(routine)
        return routine

    return wrapper


def send(routine, value):
    """Send value to coroutine without raising"""
    try:
        routine.send(value)
    except StopIteration:
        return False
    else:
        return True


@coroutine
def conversation(start):
    """Manages standing user conversation"""
    while True:
        update = yield
        routine = start(update)
        while send(routine, update):
            update = yield


def _format_base(station, attr, bordername, format):
    if not station.enabled:
        return 'Estación no disponible en {!r}'.format(station)

    if not getattr(station, attr):
        return 'Estación {} en {!r}'.format(bordername, station)

    return format(station)


def plural(singular, count, suffix='s', plural=None):
    if count == 1:
        return singular

    return singular + suffix if plural is None else plural


def format_bikes(station):
    def format(station):
        return '{n} {name} en {station!r}'.format(
            n=station.bikes, name=plural('bici', station.bikes),
            station=station)

    return _format_base(station, 'bikes', 'vacía', format)


def format_spaces(station):
    def format(station):
        return '{n} {name} en {station!r}'.format(
            n=station.spaces, name=plural('plaza', station.spaces),
            station=station)

    return _format_base(station, 'spaces', 'a tope', format)


def format_station(station):
    if not station.enabled:
        return 'Estación no disponible en {!r}'.format(station)

    return '- {bikes} {bike} y {spaces} {space} en {station!r}'\
        .format(bikes=station.bikes, bike=plural('bici', station.bikes),
                spaces=station.spaces, space=plural('plaza', station.spaces),
                station=station)


def format_station_area(station):
    if not station.enabled:
        return 'Estación no disponible a {}m en {!r}'.format(
            int(station.distance), station)

    return '- {bikes} {bike} y {spaces} {space} a {m}m\n  en {station!r}'\
        .format(bikes=station.bikes, bike=plural('bici', station.bikes),
                spaces=station.spaces, space=plural('plaza', station.spaces),
                m=int(station.distance), station=station)


@coroutine
def command_start(telegram, bicimad):
    update = yield
    response = "¡Hola! Puedo echarte un cable para encontrar \
        una bicicleta. Comparte conmigo tu posición y te diré \
        las que tienes más cerca"
    telegram.send_message(update.chat_id, response)


def divide_stations(bicimad, stations, queryname):
    """Divide int good, bad stations"""
    good = getattr(bicimad.stations, queryname)(stations)
    return good, set(stations) - set(good)


def make_search_command(name, format, queryname):
    """Builds generic search stations by text/id

    It uses different queries and output formatting but the logic and messages
    are mostly the same.

    :returns: command handler function
    """

    @coroutine
    def function(telegram, bicimad):
        update = yield
        arguments = update.arguments

        if not arguments:
            response = 'Comparte tu posición o dime el número '\
                'o la dirección para buscar.'

            telegram.send_message(update.chat_id, response, force_reply=True)
            update = yield
            arguments = getattr(update, 'text', '')

        if arguments.isdigit():
            response = make_id_query_response(int(arguments), bicimad, format)
        elif update.type == 'location':
            response = make_location_response(update, bicimad, queryname)
        else:
            response = make_query_response(
                arguments, bicimad, format, queryname)

        telegram.send_message(update.chat_id, response)

    return function


def make_id_query_response(sid, bicimad, format):
    station = bicimad.stations.by_id(sid)

    if station is None:
        response = 'Mmmm, no hay ninguna estación '\
            'con id {}. Prueba con el nombre.'.format(sid)
    else:
        response = 'La estación número {} es la que está en {}:\n\n{}'\
            .format(sid, station.address, format(station))

    return response


def make_query_response(arguments, bicimad, format, queryname):
    stations = bicimad.stations.by_search(arguments)

    if not stations:
        response = 'Uhh no me suena esa dirección para '\
            'ninguna estación. Afina un poco más.'
    else:
        response = ''

        good, bad = divide_stations(bicimad, stations, queryname)

        # Valid search results
        if good:
            response += 'Pues puede que sea alguna de estas:\n\n'\
                + '\n'.join(map(format, good))

        # separator
        if good and bad:
            response += '\n\n'

        # Valid search results but empty or unavailable
        if bad:
            response += 'Estas me salen pero no creo '\
                'que te sirvan de mucho:\n\n'\
                + '\n'.join(map(format, bad))

    return response


command_bici = make_search_command('bici', format_bikes, 'with_bikes')
command_plaza = make_search_command('plaza', format_spaces, 'with_spaces')
command_estacion = make_search_command('estacion', format_station, 'with_some_use')


@coroutine
def command_help(telegram, bicimad):
    update = yield
    response = 'Puedo ayudarte a encontrar una bici si me '\
        'preguntas con cariño.\n\n'\
        '* Puedes buscar una estación buscando por nombre '\
        'por ej: "/bici atocha"\n'\
        '* Es mucho más rápido darle a "compartir posición" y te '\
        'diré todas las que tienes alrededor.\n\n'\
        'Vamos poco a poco añadiendo más posibilidades :)'
    telegram.send_message(update.chat_id, response)


@coroutine
def command_unknown(telegram, bicimad):
    update = yield
    response = "No reconozco esa orden"
    telegram.send_message(update.chat_id, response, reply_to=update.message_id)


command_handlers = dict(
    start=command_start,
    bici=command_bici,
    plaza=command_plaza,
    help=command_help,
    estacion=command_estacion,
)


@coroutine
def process_command_message(telegram, bicimad):
    update = yield
    log.info(u'%r Got command: %s from: %r',
             update, update.command, update.sender)

    handler = command_handlers.get(update.command, command_unknown)
    routine = handler(telegram, bicimad)
    while send(routine, update):
        update = yield


@coroutine
def process_text_message(telegram, bicimad):
    update = yield
    log.info('%r Got message from %r: %s',
        update, update.sender, update.text)


def make_location_response(update, bicimad, queryname):
    lat, long = update.location
    log.info(u'%r Got location from %r: lat: %f long: %f',
        update, update.sender, lat, long)

    stations = bicimad.stations.by_distance(update.location)
    good, bad = divide_stations(bicimad, stations, queryname)

    message = ''
    if good:
        message = 'Las estaciones que te pillan más a mano son:\n\n'\
            + '\n'.join(map(format_station_area, good))

    if good and bad:
        message += '\n\n'

    if bad:
        message += 'Estas están cerca, pero como si no estuvieran:\n\n'\
            + '\n'.join(map(format_station_area, bad))

    return message


@coroutine
def process_location_message(telegram, bicimad):
    update = yield
    message = make_location_response(update, bicimad, 'with_some_use')
    telegram.send_message(update.chat_id, message, reply_to=update.message_id)


def process_message(update, telegram, bicimad, conversations={}):
    """Process a new update"""

    # Get or create conversation
    convers = conversations.get(update.sender.id)
    if convers is None:
        log.info('Starting conversation with %r', update.sender)
        convers = conversation(
            lambda update: start_conversation(update, telegram, bicimad))
        conversations[update.sender.id] = convers

    # next conversation step
    if not send(convers, update):
        del conversations[update.sender.id]
        log.error('Finished conversation %r', update.sender.id)


def start_conversation(update, telegram, bicimad):
    """starts conversation type from first update message"""
    if update.type == 'text':
        return process_text_message(telegram, bicimad)

    elif update.type == 'command':
        return process_command_message(telegram, bicimad)

    elif update.type == 'location':
        return process_location_message(telegram, bicimad)

    else:
        log.info(u'(update: %d chat: %d) Unmanaged message from %r: %s',
                update.id, update.chat_id, update.sender, update.message)
        telegram.send_message(update.chat_id, u'No te pillo')
