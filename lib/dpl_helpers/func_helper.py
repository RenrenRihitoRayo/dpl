if __name__ != "__dpl_require__":
    raise Exception("This must be included by a DuProL Extension script!")


def has_repr(obj):
    return "_internal" in obj and "_im_repr" in obj


def get_repr(func):
    frame = dpl.varproc.new_frame()
    dpl.varproc.nscope(frame)
    frame[-1]["_returns"] = ["result"]
    if func["self"] != dpl.state.bstate("nil"):
        frame[-1]["self"] = func["self"]
    err = dpl.run_code(func["body"], frame=frame)
    if err > 0:
        raise Exception(err)
    return frame[0].get("result", dpl.constants.none)
