if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

if not dpl.info.VERSION.isLater((1, 4, None)):
    raise Exception("This is for version 1.4.x!")

type_vars = dpl.extension()


def check(var, value):
    try:
        return True if isinstance(value, var["type"]) else False
    except:
        raise Exception("Type mismatch!")


@type_vars.add_func()
def defv(frame, _, name, value_type):
    dpl.varproc.rset(
        frame[-1], name, {"type": value_type, "[meta_value]": value_type()}
    )


@type_vars.add_func()
def setv(frame, _, name, value):
    old = dpl.varproc.rget(frame[-1], name, meta=False)
    if old == dpl.state_nil:
        return f"err:{dpl.error.NAME_ERROR}:Variable {name!r} is not defined!"
    else:
        if not check(old, value):
            return f"err:{dpl.error.TYPE_ERROR}:Variable {name!r} expects type {old['type']} but got {type(value)} ({value!r})"
        dpl.varproc.rset(frame[-1], name, value)
