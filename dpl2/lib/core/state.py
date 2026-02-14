# Implementation of the bstate class
# It isnt related to the state of the interpreter!
# That is handled across multiple modules
# This is what the 'nil' and 'none' values
# are, just bstate instances.


class bstate:
    def __init__(self, name, bool_value=False):
        self.name = name
        self.bool = bool_value

    def __eq__(self, other):
        if not isinstance(other, bstate):
            return False
        return other.name == self.name

    def __ne__(self, other):
        return not self == other

    def __bool__(self):
        return self.bool

    def __repr__(self):
        return f"<{self.name}>"

    def __hash__(self):
        return hash(repr(self))

    def __add__(self, other):
        return self

    def __sub__(self, other):
        return self

    def __mul__(self, other):
        return self

    def __div__(self, other):
        return self

    def __fdiv__(self, other):
        return self

    def __abs__(self, other):
        return self

    def __pow___(self, other):
        return self

    def __truediv__(self, other):
        return self

    def __divmod__(self, other):
        return self

    def __and__(self, other):
        return self

    def __or__(self, other):
        return self

    def __not__(self):
        return not self.bool

    def __lt__(self, other): return self
    def __le__(self, other): return self
    def __gt__(self, other): return self
    def __ge__(self, other): return self

    def __add__(self, other): return self
    def __radd__(self, other): return self
    def __sub__(self, other): return self
    def __rsub__(self, other): return self
    def __mul__(self, other): return self
    def __rmul__(self, other): return self
    def __truediv__(self, other): return self
    def __rtruediv__(self, other): return self
    def __floordiv__(self, other): return self
    def __rfloordiv__(self, other): return self
    def __mod__(self, other): return self
    def __rmod__(self, other): return self
    def __pow__(self, other): return self
    def __rpow__(self, other): return self
    def __and__(self, other): return self
    def __rand__(self, other): return self
    def __or__(self, other): return self
    def __ror__(self, other): return self
    def __xor__(self, other): return self
    def __rxor__(self, other): return self
    def __lshift__(self, other): return self
    def __rlshift__(self, other): return self
    def __rshift__(self, other): return self
    def __rrshift__(self, other): return self

    # Unary operators
    def __neg__(self): return self
    def __pos__(self): return self
    def __invert__(self): return self
    def __abs__(self): return self

    # Length (optional, usually nil doesn't have length)
    def __len__(self): return 0

class Nil:
    def __new__(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance  # singleton

    def __repr__(self):
        return "nil"

    def __bool__(self):
        return False

    def __call__(self, *args, **kwargs):
        return self

    def __getattr__(self, name):
        return self

    def __setattr__(self, name, value):
        pass

    def __getitem__(self, key):
        return self

    def __setitem__(self, key, value):
        pass

    def __iter__(self):
        return iter([])

    def __contains__(self, item):
        return False

    # Arithmetic and comparison



