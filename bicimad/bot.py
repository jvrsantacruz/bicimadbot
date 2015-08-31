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


def process_message(update_id, message, telegram, bicimad):
    user, chat, text, location = unpack_message(message)
    chat_id = chat['id']

    if text:
        if text.startswith('/'):
            command = text.split(' ', 1)[0]
            arguments = text.split(' ', 1)[1:]

            # start command
            if command == '/start':
                response = "¡Hola! Puedo echarte un cable para encontrar \
                    una bicicleta. Comparte conmigo tu posición y te diré \
                    las que tienes más cerca"

            # bici command
            elif command == '/bici':
                if not arguments or not arguments[0].strip():
                    response = 'No me has dicho por qué buscar. '\
                        'Pon "/bici Sol", por poner un ejemplo, '\
                        'o comparte tu posición, y terminamos antes.'
                else:
                    if to_int(arguments[0]):
                        sid = to_int(arguments[0])
                        station = bicimad.stations\
                            .with_bikes_by_id(sid)
                        if station is None:
                            response = 'Mmmm, no hay ninguna estación '\
                                'con id {}. Prueba con el nombre.'.format(sid)
                        else:
                            response = 'La estación con id {} '\
                                'es la que está en {}:\n\n{}'\
                                .format(sid, station.direccion,
                                        format_bikes(station))
                    else:
                        stations = bicimad.stations\
                            .with_bikes_by_search(arguments[0])
                        if not stations:
                            response = 'Uhh no me suena esa dirección para '\
                                'ninguna estación. Afina un poco más.'
                        else:
                            response = 'Pues puede que sea alguna de estas:\n\n'\
                                + '\n'.join(map(format_bikes, stations))

            # plaza command
            elif command == '/plaza':
                if not arguments or not arguments[0].strip():
                    response = 'No me has dicho por qué buscar. '\
                        'Pon "/bici Sol", por poner un ejemplo, '\
                        'o comparte tu posición, y terminamos antes.'
                else:
                    if to_int(arguments[0]):
                        sid = to_int(arguments[0])
                        station = bicimad.stations\
                            .with_spaces_by_id(sid)
                        if station is None:
                            response = 'Mmmm, no hay ninguna estación '\
                                'con id {}. Prueba con el nombre.'.format(sid)
                        else:
                            response = 'La estación con id {} '\
                                'es la que está en {}:\n\n{}'\
                                .format(sid, station.direccion,
                                        format_spaces(station))
                    else:
                        stations = bicimad.stations\
                            .with_spaces_by_search(arguments[0])
                        if not stations:
                            response = 'Uhh no me suena esa dirección para '\
                                'ninguna estación. Afina un poco más.'
                        else:
                            response = 'Pues puede que sea alguna de estas:\n\n'\
                                + '\n'.join(map(format_spaces, stations))

            # help command
            elif command == '/help':
                response = 'Puedo ayudarte a encontrar una bici si me '\
                    'preguntas con cariño.\n\n'\
                    '* Puedes buscar una estación buscando por nombre '\
                    'por ej: "/bici atocha"\n'\
                    '* Es mucho más rápido darle a "compartir posición" y te '\
                    'diré todas las que tienes alrededor.\n\n'\
                    'Vamos poco a poco añadiendo más posibilidades :)'

            # estacion command
            elif command == '/estacion':
                response = "Estos comandos funcionarán próximamente"

            # unknown command
            else:
                response = "No reconozco esa orden"

            log.info(u'(update: %d chat: %d) Got command: %s from: %s',
                        update_id, chat_id, text, repr_user(user))
            telegram.send_message(chat_id, response)
            return

        log.info('(update: %d chat: %d) Got message from %s: %s',
                    update_id, chat_id, repr_user(user), text)

    elif location:
        lat, long = unpack_location(location)
        log.info(u'(update: %d chat: %d) Got location from %s: lat: %f long: %f',
                    update_id, chat_id, repr_user(user), lat, long)

        stations = bicimad.stations.with_bikes_by_distance((lat, long))
        message = ('Las bicis que te pillan más cerca son:\n\n'
                   + '\n'.join(map(format_bikes, stations)))
        telegram.send_message(chat_id, message)
    else:
        log.info(u'(update: %d chat: %d) Unmanaged message from %s: %s',
                    update_id, chat_id, repr_user(user), message)
        telegram.send_message(chat_id, u'No te pillo')
