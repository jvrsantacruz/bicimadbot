# -*- coding: utf-8 -*-
import os
import json
import time
import logging

import click
from bottle import ConfigDict

from . import bicimad
from . import telegram

log = logging.getLogger('bicimad.cli')
output_format = '%(asctime)s %(name)s %(levelname)-8s %(message)s'
verbosity_levels = [logging.ERROR, logging.INFO, logging.DEBUG]
min_verbosity = 0
max_verbosity = len(verbosity_levels) - 1


def get_verbosity_level(index):
    """Give a logging level from 0 (ERROR) to 2 (DEBUG)"""
    return verbosity_levels[max(0, min(2, index))]


def setup_logging(verbosity):
    level = get_verbosity_level(verbosity)
    logging.basicConfig(level=level, format=output_format)


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
def telegram_cli():
    """Telegram commands"""
    setup_logging(2)


@telegram_cli.command()
@click.option('-o', '--offset', default=0)
def updates(offset):
    """See pending updates from given offset"""
    config = get_config()
    if offset:
        config['telegram.offset'] = offset

    click.echo('offset: {}'.format(config.get('telegram.offset')))
    tgram_api = telegram.Telegram.from_config(config)
    updates = tgram_api.get_updates(config.get('telegram.offset'))
    click.echo(json.dumps(updates, indent=4, sort_keys=True))
    click.echo('offset: {}'.format(config.get('telegram.offset')))


@telegram_cli.command()
@click.option('-o', '--offset', default=0)
def update(offset):
    """Telegram test api"""
    process_updates(offset)
    click.secho('Done', fg='green')


@telegram_cli.command()
@click.option('--offset', default=0)
@click.option('-s', '--sleep', default=30)
def poll(offset, sleep):
    """Telegram test api"""
    while True:
        try:
            process_updates(offset)
        except KeyboardInterrupt:
            raise click.ClickError(u'Exiting')
        except Exception as error:
            msg = u'Catched error: {}'.format(str(error))
            log.exception(msg)
            click.secho(msg, fg='red')

        time.sleep(sleep)


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


def get_config():
    config = ConfigDict().load_config(os.getenv(u'APP_CONFIG'))
    get_offset(OFFSET_FILE, config)
    return config


def process_updates(offset):
    config = get_config()
    if offset:
        config['telegram.offset'] = offset

    tgram_api = telegram.Telegram.from_config(config)
    bmad_api = bicimad.BiciMad.from_config(config)
    updates = tgram_api.get_updates(config.get('telegram.offset'))
    telegram.process_updates(updates, config, tgram_api, bmad_api)

    save_offset(OFFSET_FILE, config)
