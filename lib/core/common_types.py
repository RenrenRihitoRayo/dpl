import collections
from . import constants

class ID:
    __slots__ = ("name", "split", "as_class_method", "read", "path_len", "hashed")
    def __init__(self, name, read=None):
        self.name = name
        self.split = name.split(".") # memory hungry but faster
        self.as_class_method = (self.split[0], ".".join(self.split[1:]))
        self.read = read
        self.path_len = len(self.split)
        self.hashed = hash(name)
        # read can be
        # norm = normal variable read
        # spec = special variable read
        # None = treat as a normal string
    def startswith(self, other):
        return self.name.startswith(other)
    def endswith(self, other):
        return self.name.endswith(other)
    def __getitem__(self, other):
        return self.name.__getitem__(other)
    def __eq__(self, other):
        return self.name == other
    def __ne__(self, other):
        return self.name != other
    def __hash__(self):
        return self.hashed
    def __mul__(self, other):
        return self.name * other
    def __add__(self, other):
        return self.name + other
    def __contains__(self, other):
        return other in self.name
    def __repr__(self):
        if self.read:
            return f"<{self.name}-{self.read}>"
        else:
            return self.name

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
    def __init__(self, data=None):
        super().__init__(lambda: constants.nil)
        if data is not None:
            self.update(data)
    def __repr__(self):
        return f"<shrunk ({', '.join(map(str, self.keys()))})>"
