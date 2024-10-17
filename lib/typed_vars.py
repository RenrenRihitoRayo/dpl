# Implements typed vars in DPL

if __name__ != "__dpl__":
    raise Exception

varproc.modules["types"] = {
    "string":str,
    "integer":int,
    "float":float,
    "dictionary":dict,
    "list":list
}

@add_func()
def defv(frame, _, name, v_type, value=None):
    if value is not None and not isinstance(value, v_type):
        raise RuntimeError("Invalid type!")
    varproc.rset(frame[-1], name, {
        "[meta_value]":value if value is not None else state.bstate("none"),
        "type":v_type
    })

@add_func()
def setv(frame, _, name, value):
    temp = varproc.rget(frame[-1], name, meta=False)
    if not isinstance(temp, dict) or "[meta_value]" not in temp or "type" not in temp:
        return
    if not isinstance(value, temp["type"]):
        raise RuntimeError(f"Invalid type! Expected {temp['type']} but got {type(value)}")
    else:
        temp["[meta_value]"] = value
