ext = dpl.extension(meta_name="io", alias=__alias__)
import asyncio

frame_stack[0]["io"] = data = {
    "output": modules.sys.stdout,
    "take_input": True
}

@ext.add_func("print")
def myPrint(_, __, *args, end="", sep=" "):
    "Print args, with sep inbetween, ending with end"
    print(*args, end=end, sep=sep, file=data["output"], flush=True)


@ext.add_func()
def println(_, __, *args, sep=" "):
    "Prints args, with sep inbetween, always inserts newline"
    print(*args, sep=sep, file=data["output"], flush=True)


@ext.add_func()
def debug(_, __, arg):
    "Print the debug info of an object"
    if hasattr(_, __, arg, "__dpl_repr__"):
        print(arg.__dpl_repr__())
    else:
        print(arg)


@ext.add_func("input")
def myInput(_, __, name=None, prompt=None, default=dpl.state_none):
    "Take input from the user"
    if data["take_input"]:
        res = input(prompt if prompt else "")
    else:
        print(f"[USED DEFAULT VALUE] {prompt if prompt else ''}{default}", file=data["output"])
        res = default
    if name is not None:
        dpl.varproc.rset(frame[-1], name, res)


@ext.add_func()
def setoutputfile(_, __, file):
    "Sets the output file for text"
    data["output"] = file


@ext.add_func()
def resetoutputfile(_, __):
    "Reset the output file to stdout"
    data["output"] = modules.sys.stdout


@ext.add_func()
def rawoutput(_, __, *values):
    "Does not buffer output, any int will be converted into a character via ascii code"
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
    data["output"].write("".join(s))
    data["output"].flush()


@ext.add_func()
def flush(_, __):
    "Manually flush the current output file"
    data["output"].flush()
