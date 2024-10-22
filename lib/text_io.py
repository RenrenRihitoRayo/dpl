

if __name__ != "__dpl__":
    raise Exception

@add_func()
def io(frame, _, ins, *args):
    if ins == "raw_println":
        raw_print(*args)
    elif ins == "raw_print":
        raw_print(*args, end='')
    elif ins == "raw_term_print":
        s = ""
        for i in args:
            if isinstance(i, int):
                s += chr(i)
            elif isinstance(i, str):
                s += i
            else:
                s += repr(i)
        sys.stdout.write(s)
        sys.stdout.flush()
    elif ins == "println":
        for item in args:
            if isinstance(item, dict) and "_internal" in item and "_im_repr" in item:
                varproc.nscope(frame)
                varproc.nscope(frame)
                varproc.rset(frame[-1], "self", item)
                varproc.rset(frame[-1], "_returns", ("repr",))
                err = run_code(item["_im_repr"]["body"], frame)
                if err:
                    return err
                varproc.pscope(frame)
                repr = frame[-1].get("repr", state.bstate("nil"))
                varproc.pscope(frame)
                raw_print(repr, end=' ')
            else:
                raw_print(item, end=' ')
        raw_print()
    elif ins == "print":
        for item in args:
            if isinstance(item, dict) and "_internal" in item and "_im_repr" in item:
                varproc.nscope(frame)
                varproc.nscope(frame)
                varproc.rset(frame[-1], "self", item)
                varproc.rset(frame[-1], "_returns", ("repr",))
                err = run_code(item["_im_repr"]["body"], frame)
                if err:
                    return err
                varproc.pscope(frame)
                repr = frame[-1].get("repr", state.bstate("nil"))
                varproc.pscope(frame)
                raw_print(repr, end=' ')
            else:
                raw_print(item, end=' ')
    elif ins == "input" and len(args) == 1:
        varproc.rset(frame[-1], args[0], input())
    elif ins == "flush" and len(args) == 0:
        sys.stdout.flush()
    else:
        return f"err:{error.RUNTIME_ERROR}:Invalid instruction!"

varproc.modules["py"]["io"] = io