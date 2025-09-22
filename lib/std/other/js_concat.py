import builtins

_int = int
_str = str
_float = float
_object = object
_dict = dict
_list = list
_tuple = tuple
_set = set

class jsbs:
    "Python but even more dynamic using JS tomf*ckery"
    def _to_number(self):
        try:
            return _int(self)
        except Exception:
            try:
                return _float(self)
            except Exception:
                return _float("nan")

    def _to_int32(self):
        num = int(self._to_number())
        return (num & 0xFFFFFFFF) if num >= 0 else -((-num) & 0xFFFFFFFF)

    def _to_string(self):
        try:
            return _str(self)
        except Exception:
            return f"<{self.__class__.__name__}>"

    def _coerce_pair(self, other):
        if isinstance(other, _str) or isinstance(self, _str):
            return self._to_string(), _str(other)
        if isinstance(other, _int) or isinstance(self, _int) or isinstance(other, _float) or isinstance(self, _float):
            return self._to_number(), int(other)._to_number()
        else:
            return self._to_string(), _str(other)

    def __add__(self, other):
        a, b = self._coerce_pair(other)
        return a + b

    def __radd__(self, other):
        b, a = self._coerce_pair(other)
        return a + b

    def __sub__(self, other):
        return self._to_number() - float(other)

    def __rsub__(self, other):
        return float(other) - self._to_number()

    def __mul__(self, other):
        return self._to_number() * float(other)

    def __rmul__(self, other):
        return float(other) * self._to_number()

    def __truediv__(self, other):
        return self._to_number() / float(other)

    def __rtruediv__(self, other):
        return float(other) / self._to_number()

    def __mod__(self, other):
        return self._to_number() % float(other)

    def __rmod__(self, other):
        return float(other) % self._to_number()

    def __and__(self, other):
        return self._to_int32() & int(other)

    def __rand__(self, other):
        return int(other) & self._to_int32()

    def __or__(self, other):
        return self._to_int32() | int(other)

    def __ror__(self, other):
        return int(other) | self._to_int32()

    def __xor__(self, other):
        return self._to_int32() ^ int(other)

    def __rxor__(self, other):
        return int(other) ^ self._to_int32()

    def __lshift__(self, other):
        return self._to_int32() << int(other)

    def __rlshift__(self, other):
        return int(other) << self._to_int32()

    def __rshift__(self, other):
        return self._to_int32() >> int(other)

    def __rrshift__(self, other):
        return int(other) >> self._to_int32()

    def __eq__(self, other):
        a, b = self._coerce_pair(other)
        return a == b

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        a, b = self._coerce_pair(other)
        return a < b

    def __le__(self, other):
        a, b = self._coerce_pair(other)
        return a <= b

    def __gt__(self, other):
        a, b = self._coerce_pair(other)
        return a > b

    def __ge__(self, other):
        a, b = self._coerce_pair(other)
        return a >= b

def to_builtin(cls):
    setattr(builtins, cls.__name__[1:], cls)

@to_builtin
class ndict(_dict, jsbs): ...
@to_builtin
class nlist(_list, jsbs): ...
@to_builtin
class ntuple(_tuple, jsbs): ...
@to_builtin
class nset(_set, jsbs): ...
@to_builtin
class nstr(_str, jsbs): ...
@to_builtin
class nint(_int, jsbs): ...
@to_builtin
class nfloat(_float, jsbs): ...

print(str("test") + int(90))