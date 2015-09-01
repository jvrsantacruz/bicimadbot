import logging

from .helpers import itemgetter, to_int


log = logging.getLogger('bicimad.telegram')


unpack_message = itemgetter('from', 'chat', 'text', 'location')
unpack_user = itemgetter('first_name', 'last_name', 'id')
unpack_location = itemgetter('latitude', 'longitude')
format_bikes = '{0.bikes} bicis en {0.direccion} ({0.id})'.format
format_spaces = '{0.spaces} plazas libres en {0.direccion} ({0.id})'.format


def repr_user(user):
    return 'User(name="{} {}", id={})'.format(*unpack_user(user))


def is_command(text):
    return text.startswith('/')


def parse_command(text):
    parsed = text.split(' ', 1)
    return parsed[0].strip('/'), parsed[1:]


def command_start(*args):
    return "¡Hola! Puedo echarte un cable para encontrar \
        una bicicleta. Comparte conmigo tu posición y te diré \
        las que tienes más cerca"


def make_search_command(name, format, by_id, by_search):
    """Builds generic search stations by text/id

    It uses different queries and output formatting but the logic and messages
    are mostly the same.

    :returns: command handler function
    """

    def function(update_id, chat_id, arguments, telegram, bicimad):
        if not arguments or not arguments[0].strip():
            response = 'No me has dicho por qué buscar. '\
                'Pon "/{} Sol", por poner un ejemplo, '\
                'o comparte tu posición, y terminamos antes.'.format(name)
        else:
            if to_int(arguments[0]):
                sid = to_int(arguments[0])
                station = getattr(bicimad.stations, by_id)(sid)
                if station is None:
                    response = 'Mmmm, no hay ninguna estación '\
                        'con id {}. Prueba con el nombre.'.format(sid)
                else:
                    response = 'La estación con id {} '\
                        'es la que está en {}:\n\n{}'\
                        .format(sid, station.direccion,
                                format_bikes(station))
            else:
                stations = getattr(bicimad.stations, by_search)(arguments[0])
                if not stations:
                    response = 'Uhh no me suena esa dirección para '\
                        'ninguna estación. Afina un poco más.'
                else:
                    response = 'Pues puede que sea alguna de estas:\n\n'\
                        + '\n'.join(map(format, stations))

        return response

    return function


command_bici = make_search_command(
    'bici', format_bikes, 'with_bikes_by_id', 'with_bikes_by_search')


command_plaza = make_search_command(
    'plaza', format_spaces, 'with_spaces_by_id', 'with_spaces_by_search')


def command_help(*args):
    return 'Puedo ayudarte a encontrar una bici si me '\
        'preguntas con cariño.\n\n'\
        '* Puedes buscar una estación buscando por nombre '\
        'por ej: "/bici atocha"\n'\
        '* Es mucho más rápido darle a "compartir posición" y te '\
        'diré todas las que tienes alrededor.\n\n'\
        'Vamos poco a poco añadiendo más posibilidades :)'


def command_estacion(*args):
    return "Estos comandos funcionarán próximamente"


def command_unknown(*args):
    return "No reconozco esa orden"


command_handlers = dict(
    start=command_start,
    bici=command_bici,
    plaza=command_plaza,
    help=command_help,
    estacion=command_estacion,
)


def process_text_message(update_id, chat_id, user, text, telegram, bicimad):
    if is_command(text):
        log.info(u'(update: %d chat: %d) Got command: %s from: %s',
                 update_id, chat_id, text, repr_user(user))

        command, arguments = parse_command(text)
        command_args = (update_id, chat_id, arguments, telegram, bicimad)
        response = command_handlers.get(command, command_unknown)(*command_args)

        log.info(u'(update: %d chat: %d) Sending response to %s: %s',
                 update_id, chat_id, repr_user(user), response)

        telegram.send_message(chat_id, response)
        return

    log.info('(update: %d chat: %d) Got message from %s: %s',
                update_id, chat_id, repr_user(user), text)


def process_location_message(update_id, chat_id, user, location, telegram, bicimad):
    lat, long = unpack_location(location)
    log.info(u'(update: %d chat: %d) Got location from %s: lat: %f long: %f',
                update_id, chat_id, repr_user(user), lat, long)

    stations = bicimad.stations.with_bikes_by_distance((lat, long))
    message = ('Las bicis que te pillan más cerca son:\n\n'
                + '\n'.join(map(format_bikes, stations)))
    telegram.send_message(chat_id, message)


def process_message(update_id, message, telegram, bicimad):
    user, chat, text, location = unpack_message(message)
    chat_id = chat['id']

    if text:
        process_text_message(update_id, chat_id, user, text, telegram, bicimad)

    elif location:
        process_location_message(update_id, chat_id, user, location, telegram, bicimad)

    else:
        log.info(u'(update: %d chat: %d) Unmanaged message from %s: %s',
                    update_id, chat_id, repr_user(user), message)
        telegram.send_message(chat_id, u'No te pillo')
