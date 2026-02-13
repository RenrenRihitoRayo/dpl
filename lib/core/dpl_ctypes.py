
class ctype:
    def __init__(self, name):
        self.__name = name
    def name(self, name):
        i = self.__name.find("[")
        tname, num = self.__name[:i], self.__name[i:]
        return tname + " " + name + num

class btype:
    def __init__(self, name):
        self.__name = name
    def name(self, name):
        return self.__name + " " + name
    def __mul__(self, other):
        return ctype(self.__name + f"[{other}]")

c_int = btype("int")
c_uint = btype("unsigned int")
c_double = btype("double")
c_float = btype("float")
c_byte = c_char = btype("char")
c_ubyte = btype("unsigned char")
c_short = btype("short")
c_ushort = btype("unsigned short")
c_long = btype("long")
c_ulong = btype("unsigned long")
c_bool = btype("bool")