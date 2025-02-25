if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

if not dpl.info.VERSION.isLater((1, 4, None)):
    raise Exception("This is for version 1.4.x!")

ext = dpl.extension("math")

ext["memoize"] = {}


@ext.add_method(from_func=True, process=True)
@ext.add_func()
def expr(frame, __, expression):
    res = eval(expression, {"__builtins__": {}, **frame[-1]})
    if expression not in ext["memoize"]:
        ext["memoize"][expression] = res
    return (res,)
