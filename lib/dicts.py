
if __name__ != "__dpl__":
    raise Exception

@add_func("_mods.py.dict")
def dicts(frame, _, body, obj):
    data = {}
    for _, _, name, this in body:
        if name == ".let":
            name, eq, value = argproc.exprs_runtime(frame, this)
            if eq != "=":
                raise RuntimeError("Invalid syntax!")
            data[name] = value
        elif name == ".def":
            name, = argproc.exprs_runtime(frame, this)
            data[name] = 1
        else:
            eq, *value = this
            if eq != "=":
                raise RuntimeError("Invalid syntax!")
            data[name] = argproc.exprs_runtime(frame, value)[0]
    obj.clear()
    obj.update(data)