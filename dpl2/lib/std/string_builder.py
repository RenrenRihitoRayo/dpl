from io import StringIO

ext = dpl.extension(meta_name="string_builder", alias=__alias__)


@ext.add_function()
def new(_, __):
    return StringIO(),


@ext.add_method(from_func=True)
@ext.add_function()
def write(_, __, string, value):
    string.write(str(value))


@ext.add_function()
def build(_, __, string):
    return string.getvalue(),