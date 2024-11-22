# Variable and Scope handling

import threading
import os
import sys
from . import constants
from . import info
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
    "track_time":0,
    "time_threshold":1.5,
    "_set_only_when_defined":1 # make sure that only defined variables in this scope can be set
}

# related to interpreter methods or behavior
# and meta programming to the extreme
meta = {
    "debug":debug,
    "argv":info.ARGV,
    "argc":info.ARGC,
    "internal":{
        "lib_path":info.LIBDIR,
        "main_path":"__main__",
        "version":info.VERSION,
        "raw_version":info.VERSION_TRIPLE,
        "pid":os.getpid(),
        "python_version":sys.version_info,
        "python_version_string":info.PYTHON_VER,
        "_set_only_when_defined":1
    },
    "_set_only_when_defined":1
}

meta["internal"]["libs"] = {
    "core_libs":tuple(map(lambda x: os.path.basename(x), filter(
                os.path.isfile,
                (os.path.join(info.CORE_DIR, f) for f in os.listdir(info.CORE_DIR))
            ))),
    "std_libs":tuple(map(lambda x: os.path.basename(x), filter(
                os.path.isfile,
                (os.path.join(info.LIBDIR, f) for f in os.listdir(info.LIBDIR))
            )))
}

def new_frame():
    "Generate a new scope frame"
    values_stack = []
    nscope(values_stack)
    return values_stack

def get_debug(name):
    "Get a debug option"
    return debug.get(name, None)

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
    else:
        t["_global"] = t
        t["_nonlocal"] = t
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
        if meta and isinstance(temp, dict) and "[meta_value]" in temp:
            return temp["[meta_value]"]
        else:
            return temp
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
            if meta and isinstance(node[name], dict) and "[meta_value]" in node[name]:
                return node[name]["[meta_value]"]
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
        if pos != last and name in node and isinstance(node[name], dict):
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
    if isinstance(full_name, str) and "." not in full_name:
        with W_LOCK:
            if dct.get("_set_only_when_defined") and full_name not in dct:
                error.warn(f"Tried to set {full_name!r} but scope was set to set only when defined.")
                return
            if meta and "[const]" in dct and isinstance((temp:=dct.get("[const]")), list) and full_name in temp:
                return 1
            if meta and full_name in dct and isinstance(dct[full_name], dict) and "[meta_value]" in dct[full_name]:
                dct[full_name]["[meta_value]"] = value
            else:
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
                error.warn(f"Tried to set {full_name!r} but scope was set to set only when defined.")
                return
            with W_LOCK:
                if meta and "[const]" in node and isinstance((temp:=node.get("[const]")), list) and name in temp:
                    return 1
                if meta and name in node and isinstance(node[name], dict) and "[meta_value]" in node[name]:
                    node[name]["[meta_value]"] = value
                else:
                    node[name] = value
            if is_debug_enabled("show_value_updates"):
                error.info(f"Variable {full_name!r} was set to `{value!r}`!")