ext = dpl.extension(meta_name="dl_tools")

if dpl.ffi is None:
    raise Exception("The interpreter isnt fully initiated!")

@ext.add_func()
def ctopy(_, __, string, protocol="utf-8"):
    return dpl.ffi.string(string).decode(protocol)