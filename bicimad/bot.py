import logging

from .helpers import itemgetter, to_int


log = logging.getLogger('bicimad.telegram')


unpack_user = itemgetter('first_name', 'last_name', 'id')
unpack_location = itemgetter('latitude', 'longitude')


def coroutine(function):
    """Coroutine decorator"""
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
        return 'Estación no disponible a {}m en {!r}'.format(
            int(station.distance), station)

    return '- {bikes} {bike} y {spaces} {space} a {m}m\n  en {station!r}'\
        .format(bikes=station.bikes, bike=plural('bici', station.bikes),
                spaces=station.spaces, space=plural('plaza', station.spaces),
                m=int(station.distance), station=station)


def repr_user(user):
    return 'User(name="{} {}", id={})'.format(*unpack_user(user))


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
            response = 'No me has dicho por qué buscar. '\
                'Pon "/{} Sol", por poner un ejemplo, '\
                'o comparte tu posición, y terminamos antes.'.format(name)

            telegram.send_message(update.chat_id, response, force_reply=True)
            update = yield
            arguments = update.text

        if to_int(arguments):
            sid = to_int(arguments)
            station = bicimad.stations.by_id(sid)
            if station is None:
                response = 'Mmmm, no hay ninguna estación '\
                    'con id {}. Prueba con el nombre.'.format(sid)
            else:
                response = 'La estación número {} '\
                    'es la que está en {}:\n\n{}'\
                    .format(sid, station.address, format(station))

        else:
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

        telegram.send_message(update.chat_id, response)

    return function


command_bici = make_search_command('bici', format_bikes, 'with_bikes')
command_plaza = make_search_command('plaza', format_spaces, 'with_spaces')


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
def command_estacion(telegram, bicimad):
    update = yield
    response = "Este comando funcionará próximamente"
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
    log.info(u'%r Got command: %s from: %s',
             update, update.command, repr_user(update.sender))

    handler = command_handlers.get(update.command, command_unknown)
    routine = handler(telegram, bicimad)
    while send(routine, update):
        update = yield


@coroutine
def process_text_message(telegram, bicimad):
    update = yield
    log.info('%r Got message from %s: %s',
        update, repr_user(update.sender), update.text)


@coroutine
def process_location_message(telegram, bicimad):
    update = yield
    lat, long = update.location
    log.info(u'%r Got location from %s: lat: %f long: %f',
        update, repr_user(update.sender), lat, long)

    stations = bicimad.stations.by_distance(update.location)
    good, bad = divide_stations(bicimad, stations, 'with_some_use')

    message = ''
    if good:
        message = 'Las estaciones que te pillan más a mano son:\n\n'\
            + '\n'.join(map(format_station, good))

    if good and bad:
        message += '\n\n'

    if bad:
        message += 'Estas están cerca, pero como si no estuvieran:\n\n'\
            + '\n'.join(map(format_station, bad))

    telegram.send_message(update.chat_id, message, reply_to=update.message_id)


def process_message(update, telegram, bicimad, conversations={}):
    """Process a new update"""

    # Get or create conversation
    conversation = conversations.get(update.sender['id'])
    if conversation is None:
        conversation = create_conversation(telegram, bicimad)
        conversations[update.sender['id']] = conversation

    # next conversation step
    conversation.send(update)


def create_conversation(telegram, bicimad):
    """Create user conversation"""
    return conversation(
        lambda update: start_conversation(update, telegram, bicimad))


def start_conversation(update, telegram, bicimad):
    """starts conversation type from first update message"""
    if update.type == 'text':
        return process_text_message(telegram, bicimad)

    elif update.type == 'command':
        return process_command_message(telegram, bicimad)

    elif update.type == 'location':
        return process_location_message(telegram, bicimad)

    else:
        log.info(u'(update: %d chat: %d) Unmanaged message from %s: %s',
                update.id, update.chat_id,
                repr_user(update.sender), update.message)
        telegram.send_message(update.chat_id, u'No te pillo')
