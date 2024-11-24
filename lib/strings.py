
if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

if not dpl.info.VERSION.isCompat((1, 4, 0)):
    raise Exception("This is for version 1.4.x!")

ext = dpl.extension("string")

@ext.add_func()
def split(_, __, string, delim=" ", times=-1):
    return string.split(delim, times)

@ext.add_func()
def lower(_, __, string):
    return string.lower()

@ext.add_func()
def upper(_, __, string):
    return string.upper()

@ext.add_func()
def isLower():
    return string.islower()

@ext.add_func()
def isUpper():
    return string.isupper()

@ext.add_func("myHash")
def myHash(_, __, string):
    "THIS IS NOT A PERFECT HASH FUNCTION AND JUST USES PYTHONS HASH FUNC\nTHIS WILL BE REPLACED WITH sha256 SOON"
    return hash(string)