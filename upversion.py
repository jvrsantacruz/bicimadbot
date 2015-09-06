# -*- coding: utf-8 -*-

import re
import click


VERSION_RE = r"""(\s*{name}\s*=\s*["'])([0-9.]+)(["'])"""


def compile_re(var):
    return re.compile(VERSION_RE.format(name=var))


def parse_version(path, var):
    r = compile_re(var)

    with open(path) as stream:
        version = r.search(stream.read()).group(2)

    numbers = list(map(int, version.split('.')))
    numbers += [0] * (len(numbers) - 3)  # complete N.N.N

    return tuple(numbers)


def string_version(version):
    return '.'.join(map(str, version))


def write_version(path, var, version):
    r = compile_re(var)
    version = string_version(version)

    with open(path, 'r') as stream:
        content = stream.read()

    with open(path, 'w') as stream:
        stream.write(r.subn(r'\g<1>{}\g<3>'.format(version), content)[0])


@click.group()
def cli():
    """Handle version numbers"""


def options(function):
    opts = [
        click.option('--path', default='./setup.py',
                     type=click.Path(dir_okay=False, exists=True)),
        click.option('--var', default='version'),
        click.option('--dry', is_flag=True),
        click.option('--major', is_flag=True),
        click.option('--minor', is_flag=True),
        click.option('--patch', is_flag=True)
    ]

    for option in opts:
        function = option(function)

    return function


@cli.command()
@options
def view(path, var, major, minor, patch, dry):
    change_version(parse_version(path, var), major, minor, patch)


def change_version(version, major, minor, patch):
    new_version = upversion(version, major, minor, patch)
    print('From {} to {}'.format(
        string_version(version), string_version(new_version)))
    return new_version


def upversion(version, major, minor, patch):
    if major:
        version = version[0] + 1, 0, 0

    if minor:
        version = version[0], version[1] + 1, 0

    if patch:
        version = version[0], version[1], version[2] + 1

    return version


@cli.command()
@options
def up(path, var, major, minor, patch, dry):
    new_version = change_version(parse_version(path, var), major, minor, patch)
    if not dry:
        print(u'writing {}'.format(path))
        write_version(path, var, new_version)


if __name__ == '__main__':
    cli()
