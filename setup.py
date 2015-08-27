import os
from setuptools import setup, find_packages

here = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(here, 'requirements-fixed.txt')) as stream:
    REQUIRES = stream.readlines()


setup(
    name=u'bicimad',
    version=u'2.0.0',
    description=u'BiciMad unofficial api',
    author=u'Javier Santacruz',
    author_email=u'javier.santacruz.lc@gmail.com',
    url=u'https://github.com/jvrsantacruz/bicimad',
    packages=find_packages(exclude=[u'tests', u'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=REQUIRES,
    classifiers=[
        u'Environment :: Console',
        u'Operating System :: POSIX',
        u'Development Status :: 3 - Alpha',
        u'Programming Language :: Python',
        u'Programming Language :: Python :: 3.4',
        u'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    ],
    platforms=[u'Any'],
    entry_points={
        u'console_scripts': [u'bmad = bicimad.cli:cli']
    }
)
