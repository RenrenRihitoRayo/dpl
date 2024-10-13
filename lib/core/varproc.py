# Variable and Scope handling

import threading
from .info import *
from . import state
from . import error

# lock
W_LOCK = threading.Lock()
WS_LOCK = threading.Lock()

# debug options
debug = {
    "show_instructions":0,
    "show_scope_updates":0,
    "show_value_updates":0,
    "show_imports":0,
    "log_events":0,
    "debug_output_file":"debug_log.txt",
    "_set_only_when_defined":1 # make sure that only defined variables in this scope can be set
}

# related to interpreter methods or behavior
# and meta programming to the extreme
meta = {
    "debug":debug,
    "argv":ARGV,
    "argc":ARGC,
    "internal":{
        "lib_path":LIBDIR,
        "main_path":"__main__",
        "version":0.1,
        "pid":os.getpid(),
        "_set_only_when_defined":1
    },
    "_set_only_when_defined":1
}

def new_frame():
    "Generate a new scope frame"
    values_stack = []
    nscope(values_stack)
    return values_stack

def get_debug(name):
    "Get a debug option"
    return debug.get(name, state.bstate("nil"))

def is_debug_enabled(name):
    "Return a bool if a debug option is enabled"
    return bool(debug.get(name))

def set_debug(name, value):
    "Set a debug option"
    debg[name] = value

def nscope(frame):
    "New scope"
    t = {
        "_meta":meta,
        "_temp":{}
    }
    if frame:
        t["_global"] = frame[0]
        t["_nonlocal"] = frame[-1]
    with WS_LOCK:
        frame.append(t)
    if is_debug_enabled("show_scope_updates"):
        error.info(f"New scope created!")

def pscope(frame):
    "Pop the current scope also discarding"
    if len(frame) > 1:
        with WS_LOCK:
            frame.pop()
        if is_debug_enabled("show_scope_updates"):
            error.info(f"Scope discarded!")
    else:
        if is_debug_enabled("show_scope_updates"):
            error.info(f"Tried to discard global scope!")

def rget(dct, full_name, default=state.bstate("nil"), sep="."):
    "Get a variable"
    if "." not in full_name:
        return dct.get(full_name, state.bstate("nil"))
    path = [*enumerate(full_name.split(sep), 1)][::-1]
    last = len(path)
    node = dct
    while path:
        pos, name = path.pop()
        if pos != last and name in node and isinstance(node[name], dict):
            node = node[name]
        elif pos == last and name in node:
            if is_debug_enabled("show_value_updates"):
                error.info(f"Variable {full_name!r} was read!")
            return node[name]
        else:
            return default
    return default

def rset(dct, full_name, value, sep="."):
    "Set a variable"
    if isinstance(full_name, str) and "." not in full_name:
        dct[full_name] = value
        return
    path = [*enumerate(full_name.split(sep), 1)][::-1]
    last = len(path)
    node = dct
    while path:
        pos, name = path.pop()
        if pos != last and name in node and isinstance(node[name], dict):
            node = node[name]
        elif pos == last:
            if node.get("_set_only_when_defined") and name not in node:
                error.warn(f"Tried to set {name!r} but scope was set to set only when defined.")
                return
            with W_LOCK:
                node[name] = value
            if is_debug_enabled("show_value_updates"):
                error.info(f"Variable {full_name!r} was set to `{value!r}`!")