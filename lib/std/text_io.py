ext = dpl.extension(meta_name="io", alias=__alias__)

frame_stack[0]["io"] = data = {
    "output": modules.sys.stdout,
    "take_input": True
}

@ext.add_func("print")
def myPrint(_, __, *args, end="", sep=" "):
    print(*args, end=end, sep=sep, file=data["output"], flush=True)


@ext.add_func()
def println(_, __, *args, sep=" "):
    print(*args, sep=sep, file=data["output"], flush=True)


@ext.add_func()
def debug(_, __, arg):
    if hasattr(arg, "__dpl_repr__"):
        print(arg.__dpl_repr__())
    else:
        print(arg)


@ext.add_func("input")
def myInput(frame, __, name=None, prompt=None, default=dpl.state_none):
    if data["take_input"]:
        res = input(prompt if prompt else "")
    else:
        print(f"[USED DEFAULT VALUE] {prompt if prompt else ''}{default}", file=data["output"])
        res = default
    if name is not None:
        dpl.varproc.rset(frame[-1], name, res)


@ext.add_func()
def setoutputfile(_, __, file):
    data["output"] = file


@ext.add_func()
def resetoutputfile(_, __):
    data["output"] = modules.sys.stdout


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
