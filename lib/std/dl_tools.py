if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

if not dpl.info.VERSION.isLater((1, 4, None)):
    raise Exception("This is for version 1.4.x!")

ext = dpl.extension("dl_tools")

if dpl.ffi is None:
    raise Exception("The ffi api isnt fully initiated!")

@ext.add_method()
def convert_c_string(string, protocol="utf-8"):
    return dpl.ffi.string(string).decode(protocol)