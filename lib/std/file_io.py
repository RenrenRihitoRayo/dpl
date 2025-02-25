if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

if not dpl.info.VERSION.isLater((1, 4, None)):
    raise Exception("This is for version 1.4.x!")

ext = dpl.extension(meta_name="io")


@ext.add_func("open")
def myOpen(_, local, file_name, mode="r"):
    try:
        if modules.os.path.isabs(file_name):
            file = file_name
        else:
            file = modules.os.path.join(local, file_name)
        return (open(file),)
    except Exception as e:
        return (e,)


@ext.add_func()
def seek(_, __, file_object, position, whence=0):
    file_object.seek(position, whence)


@ext.add_func()
def read(_, __, file_object):
    try:
        return (file_object.read(),)
    except Exception as e:
        file_object.close()
        return (e,)


@ext.add_func()
def write(_, __, file_object, content):
    try:
        file_object.write(content)
    except Exception as e:
        file_object.close()
        return f"err:{dpl.error.PYTHON_ERROR}:{repr(e)}"


@ext.add_func()
def append(_, __, file_object, content):
    try:
        if (mode := file_object.mode) == "a":
            file_object.append(content)
        else:
            raise Exception(
                f'Invalid operation on a file! Expected the mode to be "a" but got "{mode}"'
            )
    except Exception as e:
        file_object.close()
        return f"err:{dpl.error.PYTHON_ERROR}:{repr(e)}"


@ext.add_func()
def close(_, __, file_object):
    file_object.close()
