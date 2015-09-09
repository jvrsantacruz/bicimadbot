import logging

from .helpers import itemgetter, to_int


log = logging.getLogger('bicimad.telegram')


unpack_user = itemgetter('first_name', 'last_name', 'id')
unpack_location = itemgetter('latitude', 'longitude')
_format_station = '{0.address} ({0.id})'.format


def _format_base(station, attr, bordername, format):
    if not station.enabled:
        return 'Estación no disponible en {}'.format(_format_station(station))

    if not getattr(station, attr):
        return 'Estación {} en {}'.format(bordername, _format_station(station))

    return format(station)


def plural(singular, count, suffix='s', plural=None):
    if count == 1:
        return singular

    return singular + suffix if plural is None else plural


def format_bikes(station):
    def format(station):
        return '{n} {name} en {station}'.format(
            n=station.bikes, name=plural('bici', station.bikes),
            station=_format_station(station))

    return _format_base(station, 'bikes', 'vacía', format)


def format_spaces(station):
    def format(station):
        return '{n} {name} en {station}'.format(
            n=station.spaces, name=plural('plaza', station.spaces),
            station=_format_station(station))

    return _format_base(station, 'spaces', 'a tope', format)


def format_station(station):
    if not station.enabled:
        return 'Estación no disponible a {}m en {}'.format(
            int(station.distance), _format_station(station))

    return '- {bikes} {bike} y {spaces} {space} a {m}m\n  en {station}'.format(
        bikes=station.bikes, bike=plural('bici', station.bikes),
        spaces=station.spaces, space=plural('plaza', station.spaces),
        m=int(station.distance), station=_format_station(station))


def repr_user(user):
    return 'User(name="{} {}", id={})'.format(*unpack_user(user))


def command_start(*args):
    return "¡Hola! Puedo echarte un cable para encontrar \
        una bicicleta. Comparte conmigo tu posición y te diré \
        las que tienes más cerca"


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

    def function(update, telegram, bicimad):
        if not update.arguments:
            response = 'No me has dicho por qué buscar. '\
                'Pon "/{} Sol", por poner un ejemplo, '\
                'o comparte tu posición, y terminamos antes.'.format(name)
        else:
            if to_int(update.arguments):
                sid = to_int(update.arguments)
                station = bicimad.stations.by_id(sid)
                if station is None:
                    response = 'Mmmm, no hay ninguna estación '\
                        'con id {}. Prueba con el nombre.'.format(sid)
                else:
                    response = 'La estación número {} '\
                        'es la que está en {}:\n\n{}'\
                        .format(sid, station.address, format(station))

            else:
                stations = bicimad.stations.by_search(update.arguments)
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

    return function


command_bici = make_search_command('bici', format_bikes, 'with_bikes')
command_plaza = make_search_command('plaza', format_spaces, 'with_spaces')


def command_help(*args):
    return 'Puedo ayudarte a encontrar una bici si me '\
        'preguntas con cariño.\n\n'\
        '* Puedes buscar una estación buscando por nombre '\
        'por ej: "/bici atocha"\n'\
        '* Es mucho más rápido darle a "compartir posición" y te '\
        'diré todas las que tienes alrededor.\n\n'\
        'Vamos poco a poco añadiendo más posibilidades :)'


def command_estacion(*args):
    return "Este comando funcionará próximamente"


def command_unknown(*args):
    return "No reconozco esa orden"


command_handlers = dict(
    start=command_start,
    bici=command_bici,
    plaza=command_plaza,
    help=command_help,
    estacion=command_estacion,
)


def process_command_message(update, telegram, bicimad):
    log.info(u'%r Got command: %s from: %s',
        update, update.text, repr_user(update.sender))

    handler = command_handlers.get(update.command, command_unknown)
    response = handler(update, telegram, bicimad)

    log.info(u'%r Sending response to %s: %s',
        update, repr_user(update.sender), response)

    telegram.send_message(update.chat_id, response, reply_to=update.message_id)


def process_text_message(update, telegram, bicimad):
    log.info('%r Got message from %s: %s',
        update, repr_user(update.sender), update.text)


def process_location_message(update, telegram, bicimad):
    log.info(u'%r Got location from %s (lat,long): %r',
        update, repr_user(update.sender), update.location)

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


def process_message(update, telegram, bicimad):
    if update.type == 'text':
        process_text_message(update, telegram, bicimad)

    elif update.type == 'command':
        process_command_message(update, telegram, bicimad)

    elif update.type == 'location':
        process_location_message(update, telegram, bicimad)

    else:
        log.info(u'(update: %d chat: %d) Unmanaged message from %s: %s',
                 update.id, update.chat_id,
                 repr_user(update.sender), update.message)
        telegram.send_message(update.chat_id, u'No te pillo')
