class InvalidArgument(Exception): ...

def flags(argv, types=None, remove_first=False):
    if remove_first:
        if argv:
            argv.pop(0)
    indexes = {}
    values = {}
    flags = set()
    types = types or {}
    end = 0
    for pos, value in enumerate(argv):
        if value.startswith("-"):
            if pos > end:
                end = pos
    for pos, value in enumerate(argv):
        if value.startswith("--"):
            if "=" not in value:
                indexes[pos] = value[2:]
                flags.add(value[2:])
                continue
            indexes[pos] = value
            vname, vval = value.split("=")
            if vname[2:] in types:
                try:
                    vval = types[vname[2:]](vval)
                except:
                    raise InvalidArgument(f"{vname} was expected to be type {types[vname].__name__}.")
            values[vname[2:]] = vval
        elif value.startswith("-"):
            indexes[pos] = value[1:]
            flags.add(value[1:])
        else:
            break
    for i in indexes.keys():
        if i <= end:
            argv.pop(min(indexes.keys()))
    return set(flags), values

if __name__ == "__main__":
    from pprint import pprint
    pprint(flags([
        "--testv=woah",
        "-test",
        "-test2",
        "--myint=90",
    ],
    {
        "myint":int
    }))

if __name__ == "__dpl__":
    ext = dpl.extension(meta_name="cli_arguments")
    
    @ext.add_function("flags")
    def _(_, __, args):
        return flags(args)