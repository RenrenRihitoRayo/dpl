# Utilities for QOL functions
# Now includes DSL Config Parser

from . import arguments as argproc

try:
    import hashlib

    has_hash = True
except ImportError:
    hash_hash = False


def flatten_dict(d, parent_key="", sep="."):
    items = {}
    for key, value in d.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(flatten_dict(value, new_key, sep=sep))
        else:
            items[new_key] = value
    return items


def get_val(dct, full_name, default=0, sep="."):
    "Get a variable"
    if "." not in full_name:
        return dct.get(full_name, default)
    path = [*enumerate(full_name.split(sep), 1)][::-1]
    last = len(path)
    node = dct
    while path:
        pos, name = path.pop()
        if pos != last and name in node and isinstance(node[name], dict):
            node = node[name]
        elif pos == last and name in node:
            return node[name]
        else:
            return default
    return default


def set_val(dct, full_name, value, sep="."):
    "Set a variable"
    if "." not in full_name:
        dct[full_name] = value
        return
    path = [*enumerate(full_name.split(sep), 1)][::-1]
    last = len(path)
    node = dct
    while path:
        pos, name = path.pop()
        if pos != last and name in node and isinstance(node[name], dict):
            node = node[name]
        elif pos == last:
            node[name] = value


def constant_hash(obj):
    "Constant hash function"
    assert has_hash, "hashlib is unavailable."
    obj_representation = repr(obj).encode("utf-8")
    return hashlib.sha256(obj_representation).hexdigest()


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


def parse_config(code, format=None):
    name = None
    lines = code.split("\n")
    data = {} if format is None else format
    for line in lines:
        line = line.lstrip()
        if not line or line.startswith("#"):
            continue
        elif line == "end" and name is not None:
            name = None
        elif line.startswith("[") and line.endswith("]"):
            name = line[1:-1]
            if get_val(data, name, default=None) is None:
                set_val(data, name, {})
        else:
            ins, op, value = line.split(maxsplit=2)
            if argproc.is_int(value):
                value = int(value)
            elif argproc.is_float(value):
                value = float(value)
            elif value == "@list":
                value = []
            elif value == "@dict":
                value = {}
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            else:
                value = ""
            if op == "=":
                set_val(data, (name + "." if name is not None else "") + ins, value)
            elif op == "append":
                temp = get_val(data, (name + "." if name is not None else "") + ins)
                if temp is not None:
                    temp.append(value)
                else:
                    set_val(
                        data, (name + "." if name is not None else "") + ins, [value]
                    )
            else:
                pass
    return data
