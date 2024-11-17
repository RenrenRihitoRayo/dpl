
@add_func("_mods.py.panic")
def panic(_, file, text="Error", code=error.PANIC_ERROR):
    return f"err:{code}:{text}"

@add_func(name="_mods.py.assert")
def assert_func(_, file, condition, text="Assert failed!", error_code=error.ASSERT_ERROR):
        if not condition:
            return f"err:{error_code}:{text}"