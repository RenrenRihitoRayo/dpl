# Variable and Scope handling

import threading
import os
import sys
from . import constants
from . import info
from . import state
from . import error
from . import type_checker


# locks
# ensures the interpreter is thread safe
W_LOCK = threading.Lock()
WS_LOCK = threading.Lock()

dependencies = {"dpl": set(), "python": {}, "lua": {}}

# debug options
# some features here maybe separated
debug = {
    "type_checker": 0,
    "TC_DEFAULT_WHEN_NOT_FOUND": 1,
    "allow_automatic_global_name_resolution":1, # set to false to get variables faster
    "show_scope_updates": 0, # show when scope is popped or pushed onto
    "show_value_updates": 0, # show when variables are read or changed
    "show_imports": 0,       # show imoports and includes
    "warn_no_return": 0,     # warn about cathing python functions even when theres no return value
    "log_events": 0,         # log output (redirects to log file)
    "debug_output_file": "debug_log.txt",
    "track_time": 0,         # track function time
    "time_threshold": 1.5,   # if track_time is on and the time passes this threshhold it primts a warning saying the function took too long
    "disable_nil_values": 0, # raises an error when nil values are accessed. useful for debugging missing values.
    "error_on_undefined_vars": 0, # "NameError" like errors when variables that do not exist are read.
    "warn_undefined_vars": 1,     # Like "error_on_undefined_vars" but a warning instead.
    "_set_only_when_defined": 1,  # make sure that only defined variables in this scope can be set.
}

flags = set()

# related to interpreter methods or behavior
# and meta programming to the extreme
# this exposes as much internal data as possible
# the interpreter must fetch its info from here
# at least on runtime
meta = {
    "debug": debug,
    "argv": info.ARGV,
    "argc": info.ARGC,
    "inter_flags": flags,
    "internal": {
        "main_path": constants.none,
        "main_file": "__main__",
        "version": info.VERSION,
        "raw_version": info.VERSION_TRIPLE,
        "pid": os.getpid(),
        "python_version": str(sys.version_info),
        "python_version_string": info.PYTHON_VER,
        "_set_only_when_defined": 1,
        "implementation":"python" # python - full python impl, non-python - uses another language for parser
    },
    "dependencies": dependencies,
    "err": {"defined_errors": tuple()},
    "_set_only_when_defined": 1,
    "type_signatures":type_checker.typed
}


def set_lib_path(_, __, path):
    info.LIBDIR = path

def get_lib_path(_, __, path):
    return info.LIBDIR,

# Use this since programs might use
# info.LIBDIR rather than meta["internal"]["lib_path"]
meta["internal"]["set_lib_path"] = set_lib_path
meta["internal"]["get_lib_path"] = get_lib_path

def new_frame():
    "Generate a new scope frame"
    t = {"_meta": meta}
    t["_global"] = t
    t["_nonlocal"] = t
    t["_local"] = t
    values_stack = [t]
    t["_frame_stack"] = values_stack
    return values_stack


def get_debug(name):
    "Get a debug option"
    return debug.get(name, None)


def is_debug_enabled(name):
    "Return a bool if a debug option is enabled"
    return bool(debug.get(name))


def set_debug(name, value):
    "Set a debug option"
    debug[name] = value


def nscope(frame):
    "New scope"
    t = {"_meta": meta}
    if frame:
        t["_global"] = frame[0]
        t["_nonlocal"] = frame[-1]
        t["_local"] = t
        t["_frame_stack"] = frame
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


def rget(dct, full_name, default=constants.nil, sep=".", meta=True):
    "Get a variable"
    if "." not in full_name:
        temp = dct.get(full_name, default)
        if is_debug_enabled("show_value_updates"):
            error.info(f"Variable {full_name!r} was read!")
        else:
            return temp
    path = [*enumerate(full_name.split(sep), 1)][::-1]
    last = len(path)
    node = dct
    while path:
        pos, name = path.pop()
        if (
            pos != last
            and name in node
            and isinstance(node[name], dict)
        ):
            node = node[name]
        elif pos == last and name in node:
            if is_debug_enabled("show_value_updates"):
                error.info(f"Variable {full_name!r} was read!")
            else:
                return node[name]
        else:
            return default
    return default


def rpop(dct, full_name, default=constants.nil, sep="."):
    "Pop a variable"
    if "." not in full_name:
        with W_LOCK:
            temp = dct.get(full_name, default)
        return temp
    path = [*enumerate(full_name.split(sep), 1)][::-1]
    last = len(path)
    node = dct
    while path:
        pos, name = path.pop()
        if (
            pos != last
            and name in node
            and isinstance(node[name], dict)
        ):
            node = node[name]
        elif pos == last and name in node:
            if is_debug_enabled("show_value_updates"):
                error.info(f"Variable {full_name!r} was popped!")
            with W_LOCK:
                return node.pop(name)
        else:
            return default
    return default


def rset(dct, full_name, value, sep=".", meta=True):
    "Set a variable"
    if not isinstance(full_name, str):
        return
    if "." not in full_name:
        with W_LOCK:
            if dct.get("_set_only_when_defined") and full_name not in dct:
                error.warn(
                    f"Tried to set {full_name!r} but scope was set to set only when defined."
                )
                return
            dct[full_name] = value
            return
    path = [*enumerate(full_name.split(sep), 1)][::-1]
    last = len(path)
    node = dct
    while path:
        pos, name = path.pop()
        if (
            pos != last
            and name in node
            and isinstance(node[name], dict)
        ):
            node = node[name]
        elif pos == last:
            if node.get("_set_only_when_defined") and name not in node:
                error.warn(
                    f"Tried to set {full_name!r} but scope was set to set only when defined."
                )
                return
            with W_LOCK:
                node[name] = value
            if is_debug_enabled("show_value_updates"):
                error.info(f"Variable {full_name!r} was set to `{value!r}`!")
