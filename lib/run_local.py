if __name__ != "__dpl__":
    raise Exception

@add_func()
def pragma(frame, file, body, other_name=None):
    if other_name is None:
        if file == "__main__":
            file = varproc.meta["internal"]["main_path"]
        if not os.path.isdir(file):
            raise RuntimeError("Cannot get the local directory!")
    else:
        file = other_name
        if not os.path.isdir(file):
            raise RuntimeError("Cannot get the local directory!")
    res_body = []
    for pos, _, ins, args in body:
        res_body.append((pos, file, ins, args))
    err = run_code(res_body, frame)
    if err:
        return err