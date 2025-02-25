if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

if not dpl.info.VERSION.isLater((1, 4, None)):
    raise Exception("This is for version 1.4.x!")

ext = dpl.extension("array")


@ext.add_method(from_func=True)
@ext.add_func()
def slice(_, __, obj, from_, to=None):
    return (obj[from_:to],)


@ext.add_method(from_func=True)
@ext.add_func()
def join(_, __, obj, obj1):
    if not isinstance(obj1, (set, list, tuple)):
        obj1 = [obj1]
    if not isinstance(obj, (set, list, tuple)):
        obj = [obj]
    return (list(obj) + list(obj1),)


@ext.add_method(from_func=True)
@ext.add_func()
def reverse(_, __, obj):
    return (obj[::-1],)
