# Implements typed vars in DPL

if __name__ != "__dpl__":
    raise Exception

varproc.modules["types"] = {
    "str":str,
    "int":int,
    "float":float,
    "dict":dict,
    "list":list
}

@add_func("def")
def define_var(frame, _, name, v_type, value=None):
    varproc.rset(frame[-1], name, {
        "%meta_value%":value if value is not None else state.bstate("none"),
        "type":v_type
    })

@add_func()
def setv(frame, _, name, value):
    temp = varproc.rget(frame[-1], name, meta=False)
    if not isinstance(temp, dict) or "%meta_value%" not in temp or "type" not in temp:
        return
    if not isinstance(value, temp["type"]):
        raise RuntimeError("Invalid type!")
    else:
        temp["%meta_value%"] = value
