if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

if not dpl.info.VERSION.isLater((1, 4, None)):
    raise Exception("This is for version 1.4.x!")

ext = dpl.extension(meta_name="cli")

@ext.add_func()
def flags(_, __):
    return modules.cli_arguments.flags(
        dpl.info.ARGV.copy(),
        remove_first=True
    )