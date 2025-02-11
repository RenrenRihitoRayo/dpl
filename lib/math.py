
if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

if not dpl.info.VERSION.isLater((1, 4, None)):
    raise Exception("This is for version 1.4.x!")

ext = dpl.extension("math")

@ext.add_method(from_func=True)
@ext.add_func()
def expr(_, __, expression):
    return eval(expression, {"__builtins__":{}}),
