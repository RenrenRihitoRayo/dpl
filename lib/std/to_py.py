if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

ext = dpl.extension(meta_name="to_py", alias=__alias__)


@ext.add_func(typed="$$ :: str")
def define(frame, __, name, func_body):
    def func(*args, **kwargs):
        dpl.varproc.nscope(frame)
        frame[-1]["args"] = args
        frame[-1]["kwargs"] = kwargs
        dpl.run_code(func_body, frame)
        res = dpl.varproc.rget(frame[-1], "_export", default=None)
        dpl.varproc.pscope(frame)
        return res
    dpl.varproc.rset(frame[-1], name, func)


@ext.add_func(typed="$$ :: dict")
def to_py(frame, _, temp):
    def func(*args):
        dpl.varproc.nscope(frame)
        if temp["defaults"]:
            for name, value in modules.itertools.zip_longest(temp["args"], args):
                if value is None:
                    dpl.varproc.rset(
                        frame[-1], name, temp["defaults"].get(name, dpl.state.bstate("nil"))
                    )
                else:
                    dpl.varproc.rset(frame[-1], name, value)
        else:
            if len(args) != len(temp["args"]):
                return 1
            for name, value in modules.itertools.zip_longest(temp["args"], args):
                dpl.varproc.rset(frame[-1], name, value)
        if temp["self"] != dpl.state.bstate("nil"):
            varproc.rset(frame[-1], "self", temp["self"])
        if temp["capture"] != dpl.state.bstate("nil"):
            varproc.rset(frame[-1], "_capture", temp["capture"])
        err = dpl.run_code(temp["body"], frame)
        if err:
            return err
        res = dpl.varproc.rget(frame[-1], "_export", default=None)
        dpl.varproc.pscope(frame)
        return res
    return (func,)
