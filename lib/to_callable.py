if __name__ != "__dpl__":
    raise Exception

@add_func("_mods.py.to_callable")
def to_callable(root_frame, __, body, name, params=tuple(), external=None):
    def temp(*args):
        frame = varproc.new_frame()
        this = dict(zip(params, args))
        frame[0].update(this)
        if external is not None:
            frame[0].update(external)
        err = run_code(body, frame)
        if err:
            return err
        return frame[0].get("export"),
    varproc.rset(root_frame[-1], name, temp)