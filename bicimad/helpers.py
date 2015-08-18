# -*- coding: utf-8 -*-


def urljoin(*fragments):
    return u'/'.join(f.strip(u'/') for f in fragments)
