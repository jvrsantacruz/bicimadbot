# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name='bicimad',
    version='0.0.1',
    description='BiciMad unofficial api',
    author='Javier Santacruz',
    author_email='javier.santacruz.lc@gmail.com',
    url='https://github.com/jvrsantacruz/bicimad',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        'requests',
    ],
    classifiers=[
        'Environment :: Console',
        'Operating System :: POSIX',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    ],
    platforms=['Any'],
    entry_points={
        'console_scripts': ['bmad = bicimad:cli']
    }
)
