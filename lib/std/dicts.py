
if __name__ != "__dpl__":
    raise Exception

if not dpl.info.VERSION.isLater((1, 4, None)):
    raise Exception("This is for version 1.4.x!")

ext = dpl.extension(meta_name="dicts")

@ext.add_func()
def make_dict(frame, file, body, dname):
    data = {}
    for [pos, file, ins, args] in body:
        if ins == "set":
            name, eq, value = dpl.arguments.process_args(frame[0], args)
            if eq != "=":
                return f"err:{dpl.error.SYNTAX_ERROR}:Syntax Error!"
            data[name] = value
        else:
            return dpl.error.SYNTAX_ERROR
    dpl.varproc.rset(frame[-1], dname, data)

@ext.add_func()
def init_dict(frame, _, dname):
    dpl.varproc.rset(frame[-1], dname, {})