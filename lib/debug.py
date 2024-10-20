
if __name__ != "__dpl__":
    raise Exception

def py_func(func):
    return add_func(frame=varproc.modules["py"])(func)

def func(func):
    return add_func(frame=varproc.modules["dpl"])(func)

@py_func
def debug_file(_, file):
    print(f"Local Directory: {file}")
