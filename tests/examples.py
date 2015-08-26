"""Load response examples"""
import os
import json
from os import path


FOLDER = path.abspath(path.join(path.dirname(__file__), '../examples'))


def load_examples():
    print('hola')
    for name in os.listdir(FOLDER):
        print(name)
        yield name.strip('.json'), json.load(open(path.join(FOLDER, name)))


EXAMPLES = dict(load_examples())
