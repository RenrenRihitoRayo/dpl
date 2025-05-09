if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

if not dpl.info.VERSION.isLater((1, 4, None)):
    raise Exception("This is for version 1.4.x!")

ext = dpl.extension("dl_tools")

dpl.ffi.cdef(dpl.info.safe_py_bindings)

if dpl.ffi is None:
    raise Exception("The ffi api isnt fully initiated!")

@dpl.ffi.callback("char* this_is_a_test(void)")
def this_is_a_test():
    return dpl.ffi.new("char[]", b"String!")

@ext.add_func()
def test_call(_, __, function):
    function(this_is_a_test)