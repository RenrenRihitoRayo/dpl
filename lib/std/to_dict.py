def _to_dict(obj):
    if isinstance(obj, (tuple, list, set, complex, float, int, str, dict)):
        return obj
    elif hasattr(obj, "__dir__"):
        dct = {}
        for i in dir(obj):
            dct[i] = getattr(obj, i)
        return dct
    elif hasattr(obj, "__dict__"):
        data = obj.__dict__
        for name, value in data.items():
            data[name] = _to_dict(value)
        return data
    return obj


ext = dpl.extension(meta_name="to_dict", alias=__alias__)


@ext.add_func(typed="$$ :: any")
def to_dict(_, __, obj):
    return (_to_dict(obj),)
