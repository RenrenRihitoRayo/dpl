import __main__


class UnimplementedError(Exception): ...


def restricted(func=None):
    def this(*_, **__):
        raise UnimplementedError(
            f"This feature{(' '+func.__name__+' ') if hasattr(func, '__name__') else ''}is restricted!"
        )

    this.__name__ = getattr(func, "__name__", "this")
    return this


restricted_builtins = __main__.__builtins__.__dict__.copy()
restricted_builtins.update(
    {"__builtins__": {"__import__": restricted(__import__), "open": restricted(open)}}
)
