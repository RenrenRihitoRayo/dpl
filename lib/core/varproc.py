# Variable and Scope handling

import threading
import os
import sys
from uuid import uuid4
from . import constants
from . import info
from . import state
from . import error

'''
{
    "func": callable(scope: dict, scope_id: int) -> None,
    "from": source # str, for ppf write "python:file:?"
}
'''
# functions called on scope create
on_new_scope = []
# functions called on scope pop
on_pop_scope = []

# dependencies (populated by module_handler.py)
dependencies = {
    "dpl": set(),
    "python": set(),
    "lua": set()
}

# debug options
debug_settings = {
    "allow_automatic_global_name_resolution":1, # set to false to get variables faster
    "show_scope_updates": 0, # show when scope is popped or pushed onto
    "show_value_updates": 0, # show when variables are read or changed
    "show_imports": 0,       # show imports and includes
    "warn_no_return": 0,     # warn about cathing python functions even when theres no return value
    "log_events": 0,         # log output (redirects to log file)
    "debug_output_file": "debug_log.txt",
    "disable_nil_values": 0, # raises an error when nil values are accessed. useful for debugging missing values.
    "error_on_undefined_vars": 0, # "NameError" like errors when variables that do not exist are read.
    "warn_undefined_vars": 1,     # Like "error_on_undefined_vars" but a warning instead.
    "_set_only_when_defined": 1,  # make sure that only defined variables in this scope can be set.
}

# preruntime flags
preprocessing_flags = {
    "DEAD_CODE_OPT": constants.true, # dead code optimization
    "EXPRESSION_FOLDING": constants.true, # expression folding
    "IGNORE_EMPTY_FUNCTIONS": constants.false, # doesnt optimize empty functions out
    "WARNINGS": constants.true, # display warnings
    "STRICT": constants.false, # treat warnings as errors
    "RUNTIME_ERRORS": constants.true, # Yep this is a thing
    "EXPERIMENTAL_LLIR": constants.false, # enable expiramental llir and new execution loop.
    "_set_only_when_defined": 1,
}

to_be_methods = set()

# Core interpreter attributes
internal_attributes = {
    "main_path": constants.none,
    "main_file": "__main__",
    "version": info.VERSION,
    "raw_version": info.VERSION_TRIPLE,
    "pid": os.getpid(),
    "python_version": str(sys.version_info),
    "python_version_string": info.PYTHON_VER,
    "implementation":"python", # the language the parser is in.
    "_set_only_when_defined": 1,
    "methods": to_be_methods
}

flags = set()

# related to interpreter methods or behavior
# and meta programming to the extreme
# this exposes as much internal data as possible
# the interpreter must fetch its info from here
# at least on runtime
meta_attributes = {
    "debug": debug_settings,
    "argv": info.ARGV,
    "argc": info.ARGC,
    "original_argv":info.original_argv,
    "interpreter_flags":info.program_flags,
    "interpreter_vflags":info.program_vflags,
    "internal": internal_attributes,
    "preprocessing_flags":preprocessing_flags,
    "dependencies": dependencies,
    "err": {},
    "_set_only_when_defined": 1,
}

error.error_setup_meta(meta_attributes)

def set_lib_path(_, __, path):
    "Set the path where global libraries are"
    info.LIBDIR = path

def get_lib_path(_, __, path):
    "Get the path where global libraries are"
    return info.LIBDIR,

# Use this since programs might use
# info.LIBDIR rather than meta_attributes"internal"]["lib_path"]
meta_attributes["internal"]["set_lib_path"] = set_lib_path
meta_attributes["internal"]["get_lib_path"] = get_lib_path

def get_important():
    "Setup."
    return {
        "meta_attributes": meta_attributes,
    }

def update_globals(stuff):
    "Setup."
    globals().update(stuff)

def new_frame():
    "Generate a new scope frame"
    t = {"_meta": meta_attributes}
    t["_global"] = t
    t["_nonlocal"] = t
    t["_local"] = t
    values_stack = [t]
    t["_frame_stack"] = values_stack
    t["_scope_uuid"] = "disabled" # global scope wont just disappear
    return values_stack


def get_debug(name):
    "Get a debug option"
    return debug_settings.get(name, None)


def is_debug_enabled(name):
    "Return a bool if a debug option is enabled"
    return bool(debug_settings.get(name))


def set_debug(name, value):
    "Set a debug option"
    debug_settings[name] = value


def nscope(frame):
    "New scope"
    t = {
        "_meta": meta_attributes,
        "_scope_uuid": str(uuid4()),
    }
    frame.append(t)
    if frame:
        t["_global"] = frame[0]
        t["_nonlocal"] = frame[-1]
        t["_frame_stack"] = frame
    t["_local"] = t
    for func in on_new_scope:
        try:
            if err:=func["func"](t, len(frame)-1):
                print(f"{func['from']}: Function raised a dpl error.")
                raise error.DPLError(err)
        except Exception as e:
            raise Exception(f"{func['from']}: Function raised an error.") from e
    if is_debug_enabled("show_scope_updates"):
        error.info(f"New scope created!")
    return t

def pscope(frame):
    "Pop the current scope also discarding"
    if len(frame) > 1:
        for func in on_pop_scope:
            try:
                if err:=func["func"](frame.pop(), len(frame)):
                    print(f"{func['from']}: Function raised a dpl error.")
                    raise error.DPLError(err)
            except Exception as e:
                raise Exception(f"{func['from']}: Function raised an error.") from e
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
            return node[name]
        else:
            return default
    return default


def rpop(dct, full_name, default=constants.nil, sep="."):
    "Pop a variable"
    if "." not in full_name:
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
            return node.pop(name)
        else:
            return default
    return default


def rset(dct, full_name, value, sep=".", meta=True):
    "Set a variable"
    if full_name == "_":
        return
    if not isinstance(full_name, str):
        return
    if "." not in full_name:
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
            node[name] = value
            if is_debug_enabled("show_value_updates"):
                error.info(f"Variable {full_name!r} was set to `{value!r}`!")
