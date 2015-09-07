# -*- coding: utf-8 -*-
import os
import json
import logging

import click
from bottle import ConfigDict

from . import bicimad
from . import telegram

log = logging.getLogger('bicimad.cli')
output_format = '%(asctime)s %(name)s %(levelname)-8s %(message)s'
verbosity_levels = [logging.ERROR, logging.INFO, logging.DEBUG]


def get_verbosity_level(index):
    """Give a logging level from 0 (ERROR) to 2 (DEBUG)"""
    return verbosity_levels[max(0, min(2, index))]


def setup_logging(verbosity):
    level = get_verbosity_level(verbosity)
    logging.basicConfig(level=level, format=output_format)


def error(message):
    raise click.ClickException(message)


@click.group()
@click.version_option()
def cli():
    """BiciMad cli"""


@cli.command()
def start():
    """Start server"""
    from .handlers import app
    app.run()


@cli.group('telegram')
@click.option('-v', '--verbose', count=True, default=0)
def telegram_cli(verbose):
    """Telegram commands"""
    setup_logging(verbose)


def telegram_options(function):
    options = [
        click.option('-o', '--offset', default=0),
        click.option('-t', '--timeout', help="poll timeout"),
        click.option('-c', '--config', type=click.Path(dir_okay=False, exists=True))
    ]

    for option in options:
        function = option(function)

    return function


@telegram_cli.command()
@telegram_options
def updates(config, offset, timeout):
    """See pending updates from given offset"""
    config, tgram_api, bmad_api = init_apis(config, offset, timeout)
    click.echo('offset: {}'.format(config.get('telegram.offset')))
    updates = tgram_api.get_updates(config.get('telegram.offset'))
    click.echo(json.dumps(updates, indent=4, sort_keys=True))
    click.echo('offset: {}'.format(config.get('telegram.offset')))


@telegram_cli.command()
@telegram_options
def update(config, offset, timeout):
    """Get new updates from the api"""
    process_updates(config, offset, timeout)
    click.secho('Done', fg='green')


@telegram_cli.command()
@telegram_options
def poll(config, offset, timeout):
    """Poll the api for new updates"""
    while True:
        try:
            process_updates(config, offset, timeout)
        except KeyboardInterrupt:
            raise click.ClickException(u'Exiting')
        except Exception as error:
            msg = u'Catched error: {}'.format(str(error))
            log.exception(msg)
            click.secho(msg, fg='red')


def save_offset(filename, config):
    with open(filename, 'w') as stream:
        json.dump({'telegram.offset': config.get('telegram.offset')}, stream)


def get_offset(filename, config):
    try:
        with open(filename) as stream:
            config.update(json.load(stream))
    except OSError:
        pass


OFFSET_FILE = '/tmp/bmad_offset.json'


def getenv(name):
    return os.getenv(name) \
        or error(u'Missing ${} environment variable'.format(name))


def get_config(path):
    config = ConfigDict().load_config(path or getenv('APP_CONFIG'))
    get_offset(OFFSET_FILE, config)
    return config


def init_apis(config, offset, timeout):
    config = get_config(config)
    if offset:
        config['telegram.offset'] = offset
    if timeout is not None:
        config['telegram.poll_timeout'] = timeout

    tgram_api = telegram.Telegram.from_config(config)
    bmad_api = bicimad.BiciMad.from_config(config)

    return config, tgram_api, bmad_api


def process_updates(config, offset, timeout):
    config, tgram_api, bmad_api = init_apis(config, offset, timeout)
    updates = tgram_api.get_updates(config.get('telegram.offset'))
    telegram.process_updates(updates, config, tgram_api, bmad_api)
    save_offset(OFFSET_FILE, config)
