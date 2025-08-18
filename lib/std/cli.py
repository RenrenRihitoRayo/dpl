ext = dpl.extension(meta_name="cli")

@ext.add_func()
def flags(_, __):
    return modules.cli_arguments.flags(
        dpl.info.ARGV.copy(),
        remove_first=True
    )