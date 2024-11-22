
if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

if not dpl.info.VERSION.isCompat((1, 4, 0)):
    raise Exception("This is for version 1.4.x!")

helper = dpl.require(["dpl_helpers", "func_helper.py"])

if helper is None:
    raise Exception("Helper func_helper.py doesnt exist!")

text_io = dpl.extension(meta_name="io")

text_io["output"] = modules.sys.stdout

@text_io.add_func("print")
def myPrint(_, __, *args, end="", sep=" "):
    args = list(args)
    for pos, arg in enumerate(args):
        if isinstance(arg, dict) and helper.has_repr(arg):
            arg[pos] = helper.get_repr(arg["_im_repr"])
    print(*args, end=end, sep=sep, file=text_io["output"])

@text_io.add_func()
def println(_, __, *args, sep=" "):
    args = list(args)
    for pos, arg in enumerate(args):
        if isinstance(arg, dict) and helper.has_repr(arg):
            args[pos] = helper.get_repr(arg["_im_repr"])
    print(*args, sep=sep, file=text_io["output"])

@text_io.add_func()
def rawprint(_, __, *args, sep=" ", end=""):
    print(*args, sep=sep, file=text_io["output"], end=end)

@text_io.add_func()
def rawprintln(_, __, *args, sep=" "):
    print(*args, sep=sep, file=text_io["output"])

@text_io.add_func("input")
def myInput(frame, __, prompt=None, name=None):
    res = input(prompt)
    if name is not None:
        dpl.varproc.rset(frame[-1], name, res)

@text_io.add_func()
def test(_, __, test):
    print(helper.has_repr(test))

@text_io.add_func()
def setOutputFile(_, __, file):
    text_io["output"] = file