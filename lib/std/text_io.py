helper = dpl.require("dpl_helpers/func_helper.py")
if isinstance(helper, Exception):
    raise helper from None
ext = dpl.extension(meta_name="io", alias=__alias__)
ext.items["output"] = modules.sys.stdout

@ext.add_func("print")
def myPrint(_, __, *args, end="", sep=" "):
    print(*args, end=end, sep=sep, file=ext.items["output"], flush=True)


@ext.add_func()
def println(_, __, *args, sep=" "):
    print(*args, sep=sep, file=ext.items["output"], flush=True)


@ext.add_func()
def debug(_, __, arg):
    if hasattr(arg, "__dpl_repr__"):
        print(arg.__dpl_repr__())
    else:
        print(arg)


@ext.add_func("input")
def myInput(frame, __, name=None, prompt=None):
    res = input(prompt if prompt not in dpl.falsy else "")
    if name is not None:
        dpl.varproc.rset(frame[-1], name, res)


@ext.add_func()
def setoutputfile(_, __, file):
    ext.items["output"] = file


@ext.add_func()
def rawoutput(_, __, *values):
    s = []
    for i in values:
        if isinstance(i, int):
            try:
                s.append(chr(i))
            except:
                s.append(str(i))
        elif isinstance(i, bytes):
            s.append(i.decode("utf-8"))
        else:
            s.append(str(i))
    modules.sys.stdout.write("".join(s))
    modules.sys.stdout.flush()


@ext.add_func()
def flush(_, __):
    modules.sys.stdout.flush()
