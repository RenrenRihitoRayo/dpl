
if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

if not dpl.info.VERSION.isCompat((1, 4, 0)):
    raise Exception("This is for version 1.4.x!")

ext = dpl.extension("string")

@ext.add_func()
def split(_, __, string, delim=" ", times=-1):
    return string.split(delim, times)