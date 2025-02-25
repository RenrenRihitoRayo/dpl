if __name__ != "__dpl_require__":
    raise Exception("This must be included by a DuProL Extension script!")


def has_repr(obj):
    return "_internal" in obj and "_im_repr" in obj


def get_repr(func):
    frame = dpl.varproc.new_frame()
    frame[0]["_returns"] = ["result"]
    if func["self"] != dpl.state.bstate("nil"):
        dpl.varproc.rset(frame[-1], "self", func["self"])
    err = dpl.run_code(func["body"], frame)
    if err:
        raise Exception(err)
    return dpl.varproc.rget(frame[0], "result")
