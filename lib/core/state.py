# Implementation of the bstate class
# It isnt related to the state of the interpreter!
# That is handled across multiple modules
# This is what the 'nil' and 'none' values
# are, just bstate instances.


class bstate:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, bstate):
            return False
        return other.name == self.name

    def __ne__(self, other):
        return not self == other

    def __bool__(self):
        return False

    def __repr__(self):
        return f"<{self.name}>"
