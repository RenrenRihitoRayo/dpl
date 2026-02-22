import collections
from . import constants

class Expression(list):
    def __hash__(self):
        return hash(str(self))
    def __str__(self):
        string = ""
        for i in self:
            if isinstance(i, CallShortened):
                string += " "+repr(i)
            elif isinstance(i, ID):
                if i.read == "norm":
                    read = ":"
                elif i.read == "spec":
                    read = "?:"
                else:
                    read = ""
                string += f" {read}{i.name}"
            elif not isinstance(i, str):
                string += " "+repr(i)
            else:
                string += f' {i!r}' if any(c in i for c in "\n\t ") else f" {repr(i)[1:-1]}"
        return f"[{string.strip()}]"
    def __repr__(self):
        string = ""
        for i in self:
            if not isinstance(i, str):
                string += " "+repr(i)
            else:
                string += f' {i!r}' if any(c in i for c in "\n\t ") else f" {repr(i)[1:-1]}"
        return f"[{string.strip()}]"

class CallShortened(Expression):
    def __repr__(self):
        _, name, args = self
        return f"[{name.name}!({repr(args)[1:-1]})]"

class Lazy(list):
    def __str__(self):
        return repr(self)
    def __repr__(self):
        return f"[lazy {self[1]!s}]"

class ShrunkFrame(collections.defaultdict):
    def __init__(self, data):
        super().__init__(lambda: constants.nil)
        self.update(data)
    def __repr__(self):
        return f"<shrunk ({', '.join(map(str, self.keys()))})>"
