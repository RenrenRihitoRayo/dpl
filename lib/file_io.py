
if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

if not dpl.info.VERSION.isCompat((1, 4, None)):
    raise Exception("This is for version 1.4.x!")

ext = dpl.extension(meta_name="io")

@ext.add_func("open")
def myOpen(_, local, file_name, mode="r"):
    try:
        if modules.os.path.isabs(file_name):
            file = file_name
        else:
            file = modules.os.path.join(local, file_name)
        return {
            "path":file,
            "[meta_value]":open(file, mode="r"),
            "error":dpl.state_none
        },
    except Exception as e:
        return {
            "path":file,
            "[meta_value]":dpl.state_none,
            "error":repr(e)
        },

@ext.add_func()
def close(_, __, file_object):
    file_object.close()