# Variable and Scope handling

import threading
import os
import sys
from uuid import uuid4
from . import constants
from . import info
from . import state
from . import error
from . import common_types

ShrunkFrame = common_types.ShrunkFrame

execute_code = None
Lazy = None
evaluate = None

def register_execute(fn):
    global execute_code
    execute_code = fn
    return fn

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
debug_settings = ShrunkFrame({
    "allow_automatic_global_name_resolution":constants.true, # set to false to get variables faster
    "show_scope_updates": constants.false, # show when scope is popped or pushed onto
    "show_value_updates": constants.false, # show when variables are read or changed
    "show_imports": constants.false,       # show imports and includes
    "warn_no_return": constants.false,     # warn about cathing python functions even when theres no return value
    "log_events": constants.false,         # log output (redirects to log file)
    "debug_output_file": "debug_log.txt",
    "disable_nil_values": constants.false, # raises an error when nil values are accessed. useful for debugging missing values.
    "error_on_undefined_vars": constants.false, # "NameError" like errors when variables that do not exist are read.
    "warn_undefined_vars": constants.true,     # Like "error_on_undefined_vars" but a warning instead.
    "_set_only_when_defined": constants.true,  # make sure that only defined variables in this scope can be set.
})

# preruntime flags
preprocessing_flags = ShrunkFrame({
    "EXPRESSION_FOLDING": constants.true,
    # Fixed expression folding,
    # more stable than before
    "DEAD_CODE_ELLIMIMATION": constants.true,
    "WARNINGS": constants.true, # display warnings
    "STRICT": constants.false, # treat warnings as errors
    "RUNTIME_ERRORS": constants.true, # Yep this is a thing
    "EXPERIMENTAL_LLIR": constants.false, # enable expiramental llir and new execution loop.
    "REPL_ON_ERROR": constants.false,
    # when enabled REPL_ON_ERROR would invoke a REPL when an error is encountered,
    # this makes it possible to investigate what may have happened.
    # on exit the error will propagate as the exit code
    "FOR_LOOP_SUBSTITUTION": constants.false,
    "_set_only_when_defined": constants.true,
})

to_be_methods = set()

# Core interpreter attributes
internal_attributes = ShrunkFrame({
    "main_path": constants.none,
    "main_file": "__main__",
    "version": info.VERSION,
    "raw_version": info.VERSION_TRIPLE,
    "pid": os.getpid(),
    "python_version": str(sys.version_info),
    "python_version_string": info.PYTHON_VER,
    "implementation": "python", # the language the parser is in.
    "_set_only_when_defined": 1,
    "methods": to_be_methods,
    "module_index": {}
})

flags = set()

# related to interpreter methods or behavior
# and meta programming to the extreme
# this exposes as much internal data as possible
# the interpreter must fetch its info from here
# at least on runtime
meta_attributes = ShrunkFrame({
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
    "file_cache": {},
    "_set_only_when_defined": constants.true,
})

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
    t = ShrunkFrame({"_meta": meta_attributes, "_scope_number": 0})
    t["_global"] = t
    t["_nonlocal"] = t
    t["_local"] = t
    values_stack = [t]
    t["_frame_stack"] = values_stack
    return values_stack


def get_debug(name):
    "Get a debug option"
    return debug_settings.get(name)


def is_debug_enabled(name):
    "Return a bool if a debug option is enabled"
    return bool(debug_settings.get(name))


def set_debug(name, value):
    "Set a debug option"
    debug_settings[name] = value


def nscope(frame):
    "New scope"
    t = ShrunkFrame({
        "_meta": meta_attributes,
    })
    if frame:
        t["_global"] = frame[0]
        t["_nonlocal"] = frame[-1]
        t["_frame_stack"] = frame
    frame.append(t)
    t["_local"] = t
    t["_scope_number"] = len(frame)-1
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
    scope = frame.pop()
    if len(frame) > 1:
        for func in on_pop_scope:
            try:
                if err:=func["func"](scope, len(frame)):
                    print(f"{func['from']}: Function raised a dpl error.")
                    raise error.DPLError(err)
            except Exception as e:
                raise Exception(f"{func['from']}: Function raised an error.") from e
        if is_debug_enabled("show_scope_updates"):
            error.info(f"Scope discarded!")
    else:
        if is_debug_enabled("show_scope_updates"):
            error.info(f"Tried to discard global scope!")


def rget(dct, full_name, default=constants.nil, meta=False, resolve=False):
    "Get a variable"
    if "." not in full_name:
        temp = dct[full_name.name]
        if not meta and isinstance(temp, Lazy):
            return evaluate([temp[0][0]], temp[1])
        return temp
    last = full_name.path_len
    node = dct
    for pos, name in enumerate(full_name.split, 1):
        if pos != last and isinstance(node[name], dict):
            node = node[name]
        elif pos == last and name in node:
            if not meta and isinstance(node[name], Lazy):
                return evaluate([node[name][0][0]], node[name][1])
            return node[name]
        else:
            break
    if resolve:
        for frame in reversed(dct["_frame_stack"][:-1]):
            res = rget(dct["_frame_stack"][0], full_name)
            if res != default:
                return res
    return default


def rexists(dct, full_name):
    if "." not in full_name:
        return full_name.name in dct
    last = full_name.path_len
    node = dct
    for pos, name in enumerate(full_name.split, 1):
        if pos != last and isinstance(node[name], dict):
            node = node[name]
        elif pos == last and name in node:
            return True
        else:
            return False
    return False


def rpop(dct, full_name, default=constants.nil):
    "Pop a variabletemp"
    if "." not in full_name:
        if full_name in dct:
            temp = dct.pop(full_name)
            return temp
        else:
            return default
    last = full_name.path_len
    node = dct
    for pos, name in enumerate(full_name.split, 1):
        if pos != last and isinstance(node[name], dict):
            node = node[name]
        elif pos == last and name in node:
            return node.pop(name)
        else:
            return default
    return default


def rset(dct, full_name, value, meta=False):
    "Set a variable"
    if "." not in full_name:
        if dct.get("_set_only_when_defined") and full_name not in dct:
            error.warn(
                f"Tried to set {full_name!r} but scope was set to set only when defined."
            )
            return
        dct[full_name] = value
        return
    last = full_name.path_len
    node = dct
    for pos, name in enumerate(full_name.split, 1):
        if pos != last and isinstance(node[name], dict):
            node = node[name]
        elif pos == last:
            if node.get("_set_only_when_defined") and name not in node:
                error.warn(
                    f"Tried to set {full_name!r} but scope was set to set only when defined."
                )
                return
            if meta:
                item = node.get(name)
                if item is None:
                    node[name] = value
                    return
                node[name] = item
                return
            node[name] = value
            if is_debug_enabled("show_value_updates"):
                error.info(f"Variable {full_name!r} was set to `{value!r}`!")
