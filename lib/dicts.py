
t = dpl.extension(meta_name="dicts")

@t.add_func()
def define(frame, _, body, name):
    dct = {}
    for _, _, op, args in body:
        if op == "let":
            vname, eq, *value = args
            if value == "...":
                value = dct
            else:
                value, = dpl.arguments.bs_thing(frame, value)
            if eq != "=":
                return f"err:{dpl.error.SYNTAX_ERROR}:Missing equal sign."
            dct[vname] = value
        elif op == "def":
            vname, = args
            dct[vname] = 1
        else:
            return f"err:{dpl.error.PANIC_ERROR}:Invalid op {op!r}"
    dpl.varproc.rset(frame[-1], name, dct)

@t.add_func()
def template(frame, _, template, **kwargs):
    dct = {}
    for name, item in kwargs.items():
        if name not in template:
            return f"err:{dpl.error.NAME_ERROR}:Name {name!r} is not in template."
        elif not isinstance(item, template[name]):
            return f"err:{dpl.error.TYPE_ERROR}:Expected {template[name]!r} but got {type(item)!r} ({item!r})"
        dct[name] = item
    for i in template.keys():
        if i not in dct:
            return f"err:{dpl.error.NAME_ERROR}:Value {i!r} is not defined!"
    return dct,