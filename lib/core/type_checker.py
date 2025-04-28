# Simplified type checker for DPL
from . import arguments as argproc
from . import constants
from . import state
from . import varproc
from typing import Any
from threading import Event, Thread, Lock

og_isinstance = isinstance

def isinstance(object, type):
    if type is Any:
        return True
    else:
        return og_isinstance(object, type)

class types:
    ident = object()
    nil = constants.nil
    none = constants.none

# instruction / function types
typed = {
}
alias = {
    "bool": int,
    "pythonBool": bool,
    "pythonNone": None,
    "ident": str,
    "scope": dict,
    "iterable":str|list|tuple|set|dict|range,
    "code":str|list
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
        if t is None:
            if not tt is None:
                return False
            continue
        elif isinstance(t, str):
            if isinstance(t, str) and not t == tt:
                return False
            continue
        elif isinstance(t, state.bstate) and not t == tt:
            return False
        elif not isinstance(tt, t):
            return False
    if not input or not pos:
        return True
    if last is Any:
        return True
    while pos < len(input):
        if not isinstance(input[pos], last):
            return False
        pos += 1
    return True

def parse_types(code):
    typed = {}
    # syntax
    # # comment
    # @ranged name :: targ0 targ1 targ2 ... targN ...
    # name :: targ0 targ1 targ2 ... targN
    # # if you have an instruction without arguments use the syntax below
    # %name
    # # it can also be done as
    # name ::
    # # but the first is cleaner
    
    # name can have a certain number of args.
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
                if not isinstance(type, str): continue
                type = type.strip()
                if not type:
                    continue
                if type in ("str", "int", "float", "dict", "set", "tuple", "list", "range", "bytes"):
                    types[i] = __builtins__[type]
                elif type == "any":
                    types[i] = Any
                elif type == "...":
                    types[i] = "..."
                elif type == "true":
                    types[i] = constants.true
                elif type == "false":
                    types[i] = constants.false
                elif type == "none":
                    types[i] = constants.none
                elif type == "nil":
                    types[i] = constants.nil
                elif type == "dpl:any":
                    types[i] = constants.any
                elif type == "thread":
                    types[i] = Thread
                elif type == "thread_event":
                    types[i] = Event
                elif type == "thread_lock":
                    types[i] = Lock
                elif "|" in type:
                    types1 = type.split("|")
                    for i, type in enumerate(types1):
                        type = type.strip()
                        if not type:
                            continue
                        if type in ("str", "int", "float", "dict", "set", "tuple", "list", "range", "bytes"):
                            types1[i] = __builtins__[type]
                        elif type == "any":
                            types1[i] = Any
                        elif type == "...":
                            types1[i] = "..."
                        elif type in alias:
                            types1[i] = alias[type]
                        elif type == "thread":
                            types1[i] = Thread
                        elif type == "thread_event":
                            types1[i] = Event
                        elif type == "thread_lock":
                            types1[i] = Lock
                        elif type == "true":
                            types1[i] = constants.true
                        elif type == "false":
                            types1[i] = constants.false
                        elif type == "none":
                            types1[i] = constants.none
                        elif type == "nil":
                            types1[i] = constants.nil
                        elif type == "dpl:any":
                            types1[i] = constants.any
                    types[i] = tuple(types1)
                elif type.startswith('"') and type.endswith('"'):
                    types[i] = type[1:-1]
                elif type in alias:
                    types[i] = alias[type]
            typed[ins.strip()] = (ranged, types)
        elif line.startswith("%"):
            typed[line[1:]] = (ranged, [])
    return typed

# builtins
typed.update(parse_types('''
fn :: str list
pub :: "fn" str list
match :: any
set :: str any
export :: "set" str any
@ranged :: str ...
for :: str "in" iterable
loop :: int
%loop[0]
while :: any
%pause
%thread[0]
thread[1] :: thread_event
new_thread_event :: str
%wait_for_threads
DEFINE_ERROR[1] :: str
DEFINE_ERROR[2] :: str int
cmd :: str
cmd[2] :: str str
tc_register :: str
module :: str
@ranged ccall :: any ...
@ranged catch :: list str any ...
@ranged ccatch :: str any ...
@ranged mcatch :: list str any ...
@ranged scatch :: list str any ...
@ranged smcatch :: list str any ...
@ranged pycatch :: list str any ...
@ranged body :: str ...
@ranged return :: any ...
@ranged freturn :: any ...
dlopen :: str str
dlclose :: any
getc :: str any
cdef :: str
template :: str
from_template :: dict
%skip
%stop
@ranged pass :: any ...
%fallthrough
@ranged pass :: any ...
sched[int] :: int
sched[float] :: float
if :: any
%ifmain
match :: any
exec :: code str list
sexec :: str code str list
@ranged safe :: str any ...
object :: str
new :: dict str
method :: dict str list
%START_TIME
%STOP_TIME
%LOG_TIME[0]
LOG_TIME :: str
exit :: int
help :: any
raise :: int
raise[2] :: int str
%dump_scope
dump_vars :: dict
tc_register :: str
enum :: str
%_intern.jump[int]
_intern.jump[2] :: int any
_intern.switch :: dict any'''))

def get_ins(ins, args):
    atypes = ",".join(types:=map(lambda x: type(x).__name__, args))
    if args and (tmp:=f"{ins}[{atypes}]") in typed:
        return tuple(types)
    elif args and (tmp:=f"{ins}[{len(args)}]") in typed:
        return typed[tmp][1]
    elif ins in typed:
        return typed[ins][1]
    return None

def check_ins(ins, args):
    atypes = ",".join(map(lambda x: type(x).__name__, args))
    if args and (tmp:=f"{ins}[{atypes}]") in typed:
        return True
    elif args and (tmp:=f"{ins}[{len(args)}]") in typed:
        return match_type(typed[tmp], args)
    elif ins in typed:
        return match_type(typed[ins], args)
    return varproc.is_debug_enabled("TC_DEFAULT_WHEN_NOT_FOUND")

def register(code):
    typed.update(parse_types(code))