# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name=u'bicimad',
    version=u'1.0.0',
    description=u'BiciMad unofficial api',
    author=u'Javier Santacruz',
    author_email=u'javier.santacruz.lc@gmail.com',
    url=u'https://github.com/jvrsantacruz/bicimad',
    packages=find_packages(exclude=[u'tests', u'tests.*']),
    install_requires=[
        u'click',
        u'geopy',
        u'bottle',
        u'requests',
    ],
    classifiers=[
        u'Environment :: Console',
        u'Operating System :: POSIX',
        u'Development Status :: 3 - Alpha',
        u'Programming Language :: Python',
        u'Programming Language :: Python :: 2',
        u'Programming Language :: Python :: 2.7',
        u'Programming Language :: Python :: 3.3',
        u'Programming Language :: Python :: 3.4',
        u'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    ],
    platforms=[u'Any'],
    entry_points={
        u'console_scripts': [u'bmad = bicimad.cli:cli']
    }
)
