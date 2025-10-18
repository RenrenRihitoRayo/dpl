# Utilities for QOL functions

import varproc

def pack(fmt, values):
    result = {}
    i = 0
    n = len(values)
    j = 0
    while i < len(fmt) and j < n:
        key = fmt[i]
        if key.startswith("..."):
            if i + 1 < len(fmt):
                next_key = fmt[i + 1].lstrip(".")
                result[key[3:]] = values[j:n - (len(fmt) - (i + 1))]
                j = n - (len(fmt) - (i + 1))
            else:
                result[key[3:]] = values[j:]
                j = n
        else:
            result[key] = values[j]
            j += 1
        i += 1
    return result

def unpack(data, fmt):
    result = []
    for key in fmt:
        if key.startswith("..."):
            val = varproc.rget(data, key[3:])
            if isinstance(val, str):
                result.extend(list(val))
            elif isinstance(val, (list, tuple)):
                result.extend(val)
            else:
                result.append(val)
        else:
            result.append(varproc.rget(data, key))
    return result

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
        return sec, "s (seconds)"
    elif sec >= 1e-3:
        return sec * 1e3, "ms (miliseconds)"
    elif sec >= 1e-6:
        return sec * 1e6, "µs (microseconds)"
    elif sec >= 1e-9:
        return sec * 1e9, "ns (nanoseconds)"
    else:
        return sec * 1e12, "ps (picoseconds)"


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
