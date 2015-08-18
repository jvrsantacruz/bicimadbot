# -*- coding: utf-8 -*-
import click
import logging


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


@cli.command()
@click.option('-s', '--offset', default=0)
def telegram(offset):
    """Telegram test api"""
    setup_logging(2)
    from .telegram import process_updates, get_updates
    process_updates(get_updates(offset), dict())
