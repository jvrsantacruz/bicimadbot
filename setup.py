import os
from setuptools import setup, find_packages

here = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(here, 'requirements-fixed.txt')) as stream:
    REQUIRES = stream.readlines()


setup(
    name='bicimad',
    version='6.0.1',
    description='BiciMad unofficial api',
    author='Javier Santacruz',
    author_email='javier.santacruz.lc@gmail.com',
    url='https://github.com/jvrsantacruz/bicimad',
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=REQUIRES,
    classifiers=[
        'Environment :: Console',
        'Operating System :: POSIX',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    ],
    platforms=['Any'],
    entry_points={
        'console_scripts': ['bmad = bicimad.cli:cli']
    }
)
