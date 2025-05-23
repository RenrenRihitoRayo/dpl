if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

ext = dpl.extension(meta_name="err")

class Option:
    def __init__(self, is_error, *args):
        self.is_error = is_error
        if not is_error:
            self.value = args[0]
        else:
            self.code = args[0]
            self.message = args[1]
    def get_error(self):
        if self.is_error:
            return f"err:{self.code}:{self.message}"
        else:
            return
    def get_value(self):
        if self.is_error:
            return (self.code, self.message)
        else:
            return self.value
    def __repr__(self):
        return f"Option({self.is_error}, {self.value if not self.is_error else f'{self.code}, {self.message!r}'})"

@ext.add_method()
def wrap_ok(_, value):
    return Option(False, value)

@ext.add_method()
def wrap_err(_, code, message):
    return Option(True, code, message)

@ext.add_func(typed="$$ :: str")
def raise_from_string(_, __, error_str):
    return error_str

@ext.add_func(typed="$$ :: any str")
def unwrap(frame, _, code, names):
    if len(names) != 2:
        return dpl.error.get_errror_string("RUNTIME_ERROR", "names must be a list of two items that contain valid identifiers!")
    if code.is_error:
        frame[-1][names[0]] = code.get_error()
    else:
        frame[-1][names[1]] = code.get_value()