# Simplified type checker for DPL
from typing import Any, Union

# instruction / function types
typed = {
}

def match_type(types, input, ranged=False):
    ranged, types = types
    if not ranged and len(types) != len(input):
        return False
    elif not ranged and "..." in types:
        return False
    last = None
    for pos, [t, tt] in enumerate(zip(types, input)):
        if t == "...": break
        last = t
        if isinstancr(t, str) and not t == tt:
            return False
        elif not isinstance(tt, t):
            return False
    while pos < len(input):
        if not isinstance(input[pos], last):
            return False
        pos += 1
    return True

def parse_types(code):
    typed = {}
    alias = {
        "bool": int,
        "pythonBool": bool,
        "identifier": str,
        "scope": dict
    }
    # syntax
    # # comment
    # @ranged name :: targ0 targ1 targ2 ... targN ...
    # name :: targ0 targ1 targ2 ... targN
    # # if you have an instruction without arguments use the syntax below
    # %name
    # # it can also be done as
    # name ::
    # # but the first is cleaner
    
    # name can have a certain nukber of args.
    # you can explicitly denote it with `name[args]`
    # for example loop has two syntax.
    # `loop` to denote an indefinite loop.
    # `loop num` to looo num times.
    # The syntax would be:
    # # for the first syntax
    # loop[0] ::
    # also
    # %loop[0]
    # # for the second syntax
    # loop :: int
    ml_comment = False
    for pos, line in enumerate(code.split("\n"), 1):
        line = line.strip()
        if ml_comment and line.endswith("--#"):
            ml_comment = False
            continue
        elif ml_comment:
            continue
        if line.startswith("#--"):
            ml_comment = True
            continue
        elif line.startswith("#") or not line:
            continue
        ranged = False
        if line.startswith("@ranged"):
            ranged = True
            _, line = line.split(maxsplit=1)
            line = line.strip()
        if "::" in line:
            ins, types = line.split("::", 1)
            types = types.split()
            for i, type in enumerate(types):
                type = type.strip()
                if not type:
                    continue
                if type in ("str", "int", "float", "dict", "set", "tuple", "list"):
                    types[i] = getattr(__builtins__, type)
                elif type == "any":
                    types[i] = Any
                elif type == "...":
                    types[i] = "..."
                elif "|" in type:
                    types1 = type.split("|")
                    for i, type in enumerate(types1):
                        type = type.strip()
                        if not type:
                            continue
                        if type in ("str", "int", "float", "dict", "set", "tuple", "list"):
                            types1[i] = getattr(__builtins__, type)
                        elif type == "any":
                            types1[i] = Any
                        elif type == "...":
                            types1[i] = "..."
                        elif type in alias:
                            types1[i] = alias[type]
                    types[i] = Union[tuple(types1)]
                elif type.startswith('"') and type.endswith('"'):
                    types[i] = type[1:-1]
                elif type in alias:
                    types[i] = alias[type]
            typed[ins.strip()] = (ranged, types)
        elif "=" in line:
            ins, type = line.split("=", 1)
            type = type.strip()
            if type in ("str", "int", "float", "dict", "set", "tuple", "list"):
                type = getattr(__builtins__, type)
            elif type == "any":
                type = Any
            elif type == "...":
                type = "..."
            elif type.startswith('"') and type.endswith('"'):
                type = type[1:-1]
            elif "|" in type:
                types1 = type.split("|")
                for i, type in enumerate(types1):
                    type = type.strip()
                    if not type:
                        continue
                    if type in ("str", "int", "float", "dict", "set", "tuple", "list"):
                        types1[i] = getattr(__builtins__, type)
                    elif type == "any":
                        types1[i] = Any
                    elif type == "...":
                        types1[i] = "..."
                    elif type in alias:
                        types1[i] = alias[type]
                    type = Union[tuple(types1)]
                type = Union[tuple(types1)]
            alias[ins.strip()] = type
        elif line.startswith("%"):
            typed[line[1:]] = (ranged, [])
    return typed

# builtins
typed.update(parse_types('''
iterable = str|list|tuple|set|dict

@ranged fn :: str ...
%end
match :: any
#--
    case, with and default are sub instructions for match,
    thus we cant check them without modifying the "parse_match" in
    arguments.py
--#
set :: str any
for :: str "in" iterable
loop :: int
%loop[0]
while :: any

'''))

print(typed)

def check_ins(ins, args):
    if (tmp:=f"ins[{len(args)}]") in typed:
        return match_type(typed[tmp], args)
    elif ins in typed:
        return match_type(typed[ins], args)
    return False