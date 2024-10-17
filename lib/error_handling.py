
@add_func()
def panic(_, file, text="Error", code=error.PANIC_ERROR):
    return f"err:{code}:{text}"

@add_func(name="assert")
def assert_func(_, file, condition, text="Assert failed!", error_code=error.PANIC_ERROR):
        if not condition:
            return f"err:{error_code}:{text}"