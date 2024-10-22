if __name__ != "__dpl__":
    raise Exception

def object_to_nested_dict(obj, seen=None):
    if seen == None:
        seen = set()
    if id(obj) in seen:
        return obj
    else:
        seen.add(id(obj))
    if isinstance(obj, dict):
        return {key: object_to_nested_dict(value, seen) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [object_to_nested_dict(value, seen) for value in obj]
    elif isinstance(obj, (int, float, str, tuple, set)):
        return obj
    else:
        if hasattr(obj, '__dict__'):
            return object_to_nested_dict(vars(obj), seen)
        else:
            return obj

@add_func("_mods.py.to_dicts")
def to_dicts(_, __, obj):
    return object_to_nested_dict(obj),