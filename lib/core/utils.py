# Utilities for QOL functions
from . import arguments as argproc


def flatten_dict(d, parent_key="", sep=".", seen=None):
    if seen is None:
        seen = set()
    items = {}
    dict_id = id(d)
    if dict_id in seen:
        return d
    seen.add(dict_id)
    for key, value in d.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(flatten_dict(value, new_key, sep, seen))
        elif not isinstance(key, str):
            continue
        else:
            items[new_key] = value
    seen.remove(dict_id)
    return items


def convert_sec(sec):
    "Convert seconds to appropriate units"
    if sec >= 1:
        return sec, "s"
    elif sec >= 1e-3:
        return sec * 1e3, "ms"
    elif sec >= 1e-6:
        return sec * 1e6, "µs"
    elif sec >= 1e-9:
        return sec * 1e9, "ns"
    else:
        return sec * 1e12, "ps"


def convert_bytes(byte):
    "Convert bytes to appropriate units"
    if byte < 1e3:
        return byte, "B"
    elif byte < 1e6:
        return byte * 1e-3, "KB"
    elif byte < 1e9:
        return byte * 1e-6, "MB"
    elif byte < 1e12:
        return byte * 1e-9, "GB"
    elif byte < 1e15:
        return byte * 1e-12, "TB"
    else:
        return byte * 1e-15, "PB"


def format_bytes(byte):
    vv, vu = convert_bytes(byte)
    return f"{vv:.2f}{vu}"


def format_seconds(byte):
    vv, vu = convert_sec(byte)
    return f"{vv:.2f}{vu}"
