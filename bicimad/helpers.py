def urljoin(*fragments):
    return u'/'.join(f.strip(u'/') for f in fragments)


def to_int(text):
    try:
        return int(text)
    except (TypeError, ValueError):
        return None
