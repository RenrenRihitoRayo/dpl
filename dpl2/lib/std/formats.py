ext = dpl.extension(meta_name="formats")

@ext.add_method(from_func=True)
@ext.add_func()
def is_identifier(_, __, text):
    return dpl.to_bool(
        text\
        .replace("-", "a")\
        .replace("_", "a")\
        .replace(":", "a")\
        .isalnum()
    ),

@ext.add_method(from_func=True)
@ext.add_func()
def is_integer(_, __, text):
    return dpl.to_bool(
        text.count("-") <= 1
        and
        text.replace("-", "").isdigit()
    ),

@ext.add_method(from_func=True)
@ext.add_func()
def is_float(_, __, text):
    return dpl.to_bool(
        text.count(".") <= 1
        and
        text\
        .replace(".", "")\
        .replace("-", "")\
        .isdigit()
    ),

# tell DPL that these are runtime only
# meaning if an expression uses this
# it cant be folded before runtime
dpl.info.RT_EXPR.update((
    "formats:is_identifer",
    "formats:is_integer",
    "formats:is_float"
))
