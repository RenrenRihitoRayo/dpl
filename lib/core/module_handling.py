# A module to help the parser call dynamically loaded functions and to load them too
# This is needed for the cythonized parser and slows down the pure python impl!
# I tried it, it still failed :)

# This will be kept
# why? modularity.
# why? to suffer. [ding ding ding correct answer!]

# Inclusion system for DPL
#
# Design rationale:
# - Only two include roots are supported: local (relative to script or absolute path) and global (dpl/lib)
# - This keeps include resolution simple, fast, and deterministic
# - Avoids overhead of searching multiple directories and prevents accidental includes
# - No priority conflicts or ambiguity in module resolution
# - If you wish to change the global library path
#   feel free to delve into info.py and change LIB_DIR
#
# If you’re thinking “but even C does it differently...” -
# well, this ain’t C, is it now?
#
# DPL’s inclusion philosophy: simplicity and clarity over legacy complexity.
# Why no legacy support? We cant let the past influence the future.
# Basically for the name of progress.

import itertools
import time
import os, sys
import traceback
from types import ModuleType
from . import fmt
from . import info
from . import error
from . import utils
from . import state
from . import objects
from . import varproc
from . import constants
from . import restricted
from . import py_argument_handler
from . import arguments as argproc
arguments_handler = py_argument_handler.arguments_handler

if "no-lupa" not in info.program_flags:
    import lupa

global_ffi = None
if "no-cffi" not in info.program_flags:
    from shlex import split as parse_line
    from cffi import FFI
    global_ffi = FFI()

def get_path(path, local=None):
    "Strictly for cdef files"
    if local is None:
        local = os.getcwd()
    if "@" in path:
        file_path, _, scope = path.partition("@")
        if scope == "global":
            return os.path.join(info.LIBDIR, file_path)
        elif scope == "local":
            return os.path.join(local, file_path)
        else:
            return os.path.join(local, path)
    else:
        return os.path.join(local, path)

def process_cdef(frame, code, local=None):
    lines = []
    data = {
        "_name": "_unloaded",
        "_version": (float("-inf"),)*3, # assume always the lowest (oldest)
        "_path": {
            "nt": None,
            "posix": None,
        },
        "_foreign": {
            "func": [],  # all types and functions
            "type": [],  # helps us build the lib scope
        },
    }
    for line in code.split("\n"):
        if line.startswith("#"):
            ins, *args = parse_line(line[1:])
            argc = len(args)
            if ins == "lib" and argc == 1:
                data["_name"] = args[0]
            elif ins == "path-nt" and argc == 1:
                data["_path"]["nt"] = get_path(args[0], local)
            elif ins == "path-posix" and argc == 1:
                data["_path"]["posix"] = get_path(args[0], local)
            elif ins.startswith("path-") and argc == 1:
                data["_path"][ins[5:]] = get_path(args[0], local)
            elif ins == "path" and argc == 1:
                data["_path"][os.name] = get_path(args[0], local)
            elif ins == "version" and argc == 1:
                data["_version"] = Version(args[0])
            elif ins in ("func", "type") and argc == 1:
                data["_foreign"][ins].append(args[0])
            else:
                ...
        else:
            lines.append(line)
    global_ffi.cdef("\n".join(lines))
    if data["_path"][os.name] and os.path.isfile(data["_path"][os.name]):
        try:
            lib = global_ffi.dlopen(data["_path"][os.name])
        except:
            print(traceback.format_exc())
            return
        for name in data["_foreign"]["func"]:
            def temp():
                fn = getattr(lib, name, "???")
                data[name] = lambda _, __, *args: (fn(*args),)
            temp()
        for name in data["_foreign"]["type"]:
            data[name] = name
    else:
        print(f"Library not found: {data['_path']}")
        return
    return data

def register_execute(func):
    dpl.execute_code = func
    return func


def register_run(func):
    dpl.run_code = func
    return func


def register_process(func):
    dpl.process_code = func
    return func


class modules:
    "Capsule for modules."

    os = os
    sys = sys
    traceback = traceback
    time = time
    itertools = itertools


class extension:
    "A class to help define methods and functions."

    def __init__(self, name=None, meta_name=None, alias=None):
        self.__func = {}  # functions
        self.__data = {}
        self._name = (
            name  # This is a scope name, dpl defined name.func_name
        )
        self.meta_name = meta_name  # while this is the mangled name, python defined "{meta_name}:{func_name}"
        if not alias is None:
            if self._name:
                self._name = alias
            elif self.meta_name:
                self.meta_name = alias
            else:
                self._name = alias

    def add_func(self, name=None, typed=None):
        "Add a function."
        def wrap(func):
            nonlocal name
            if func.__doc__ is None:
                func.__doc__ = (
                    f"Function `{self.meta_name}:{name}`"
                    if self.meta_name
                    else f"Function {self._name}.{name}"
                ) + ": Default doc string..."
            if name is None:
                name = getattr(func, "__name__", None) or "_"
            self.__func[self.mangle(name)] = (
                func
            )
            names = get_py_params(func)
            pattern = ""
            for name in names:
                if name.endswith("_xbody"):
                    pattern += "x"
                elif name.endswith("_body"):
                    pattern += "b"
            if pattern:
                info.PATTERN[name] = pattern
            return func
        return wrap

    def add_function(self, *args, **kwargs):
        return self.add_func(*args, **kwargs)

    def add_method(self, name=None, from_func=False):
        "Add a method."
        def wrap(func):
            if name is None:
                fname = func.__name__
            else:
                fname = name
            fname = self.mangle(fname)
            argproc.add_method(fname, func, from_func)
        return wrap

    def get(self, name, default=None):
        return self.__data.get(name, default)

    def mangle(self, name):
        if self._name:
            return f"{self._name}.{name}"
        elif self.meta_name:
            return f"{self.meta_name}:{name}"
        else:
            return name

    @property
    def name(self):
        return (self._name
            if not self.meta_name
            else self.meta_name)

    @property
    def is_meta(self):
        return (False
            if not self.meta_name
            else True)

    @property
    def functions(self):
        return self.__func

    @property
    def items(self):
        return self.__data

    def __repr__(self):
        return f"Extension<{self._name or f'{self.meta_name}:*'!r}>"


def require(path):
    "Import a python file in the lib dir.\nIn cases of 'dir/.../file' use ['dir', ..., 'file'],\nthis uses os.path.join to increase portability."
    mod = {
        "modules": modules,
        "dpl": dpl,
        "__import__": restricted.restricted(__import__),
    }
    if isinstance(path, (list, tuple)):
        path = os.path.join(*path)
    path = os.path.join(info.LIBDIR, path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{path!r} not found.")
    try:
        with open(path, "r") as f:
            exec(compile(f.read(), path, "exec"), mod)
        r = ModuleType(path)
        for name, value in mod.items():
            setattr(r, name, value)
        return r
    except Exception as e:
        return e


class wrap:
    def __init__(self, data):
        self.type = type(data) if not data is None else None
        self.value = data
    def __repr__(self):
        return f"wrap(type={self.type}, value={self.value!r})"

class dpl:
    require = require
    utils = utils
    varproc = varproc
    arguments = argproc
    info = info
    error = error
    state = state
    Version = info.Version
    ffi = None
    fmt = fmt
    register_error = error.register_error
    restricted = restricted
    state_nil = state.bstate("nil")
    state_none = state.bstate("none")
    constants = constants
    state_true = 1
    state_false = 0
    extension = extension
    objects = objects
    falsy = (state_nil, state_none, state_false, None, False)
    truthy = (state_true, True)
    exit = None
    wrap = wrap
    tag_handler = argproc.tag_handler
    execute = None
    
    def to_bool(obj):
        return constants.true if obj else constants.false

    def pycall(func, args, table):
        return func(*(args or []), **table)
    
    def add_matcher(name):
        def wrap(fn):
            argproc.matches[name] = fn
            return fn
        return wrap
    
    def call_dpl(env, func, args):
        varproc.nscope(env).update(zip(func["args"], args))
        env[-1]["_returns"] = ("_internal'::return",)
        err = dpl.execute(func["body"], env)
        varproc.pscope(env)
        if err > 0:
            error.DPLError(f"Function {func['name']} returned an error!")
        ret = env[-1].get("_internal::return")
        if ret is not None:
            if isinstance(ret, (list, tuple)):
                if len(ret) > 1:
                    return ret
                else:
                    return ret[0]
            else:
                return ret


def get_py_params(func):
    if not hasattr(func, "__code__"):
        return []
    co = func.__code__
    arg_count = co.co_argcount
    return co.co_varnames[:arg_count]

def dpl_import(frame, file, search_path=None, loc=varproc.meta_attributes["internal"]["main_path"]):
    variables = {}
    if not os.path.isabs(file):
        if search_path is not None:
            file = os.path.join(
                {"_std": info.LIBDIR, "_loc": loc}.get(
                    search_path, search_path
                ),
                file,
            )
        if not os.path.exists(file):
            print("Not found:", file)
            return 1
    if os.path.isdir(file):
        if os.path.isfile(files:=os.path.join(file, "include-dpl.txt")):
            res = []
            with open(files) as f:
                for line in f.readlines():
                    line = line.strip()
                    if "=>" in line:
                        line, alias = line.split("=>")
                        line = line.strip()
                        alias = alias.strip()
                    else:
                        alias = None
                    if line.startswith("#:"):
                        print(f"{files} [N/A]:",line[2:]) # for messages like deprecation warnings
                    elif line.startswith("#?"):
                        print(line[2:]) # for messages like deprecation warnings
                    elif line.startswith('#') or not line:
                        ...
                    else:
                        if (err:=dpl_import(frame, line, search_path=file, loc=loc)) is None:
                            print(f"Something went wrong while importing {line!r}")
                            return
                        frame, code = err
                        variables.update(frame)
                        res.update(code)
            return res
        else:
            print(f"python: 'include-py.txt' not found.\nTried to include a directory ({file!r}) without an include file!")
            return
    varproc.dependencies["dpl"].add(file)
    if varproc.is_debug_enabled("show_imports"):
        error.info(f"Imported {file!r}" if not alias else f"Imported {file!r} as {alias}")
    with open(file, "r") as f:
        res = dpl.process_code(f.read(), name=file)
        variables.update(res["frame"][0])
        return variables, res["code"]

def luaj_import(
    frame, file, search_path=None, loc=varproc.meta_attributes["internal"]["main_path"]
):
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    if not os.path.isabs(file):
        if search_path is not None:
            file = os.path.join(
                {"_std": info.LINDIR, "_loc": loc}.get(
                    search_path, search_path
                ),
                file,
            )
    if not os.path.isfile(file):
        print("File not found:", file)
        return 1
    if os.path.isdir(file):
        if os.path.isfile(files:=os.path.join(file, "include-lua.txt")):
            with open(files) as f:
                for line in f:
                    line = line.strip()
                    if "=>" in line:
                        line, alias = line.split("=>")
                        line = line.strip()
                        alias = alias.strip()
                    else:
                        alias = None
                    if line.startswith("#:"):
                        print(f"{files} [N/A]:",line[2:]) # for messages like deprecation warnings
                    elif line.startswith("#?"):
                        print(line[2:]) # for messages like deprecation warnings
                    elif line.startswith('#') or not line:
                        ...
                    else:
                        if luaj_import(frame, line, search_path=file, loc=loc):
                            print(f"Something went wrong while importing {line!r}")
                            return 1
            return
        else:
            print("luaj: 'include-lua.txt' not found.\nTried to include a directory ({file!r}) without an include file!")
            return 1
    if varproc.is_debug_enabled("show_imports"):
        error.info(f"Imported {file!r}")
    with open(file, "r") as f:
        try:
            lua.globals()["__dpl__"] = info.VERSION
            lua.globals()["package"]["path"] = (
                info.LIBDIR + os.sep + "?.lua;" + lua.globals()["package"]["path"]
            )
            lua.globals()["api"] = {
                "dpl": dpl,
                "modules": modules,
                "types": {"tuple": tuple, "set": set, "list": list},
            }
            lua.execute(f.read(), file)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            error.error("[N/A]", file, traceback.format_exc())
            return 1
    funcs = {}
    meths = {}
    for name in lua.globals():
        ext = lua.globals()[name]
        if isinstance(ext, extension):
            if ext.meta_name:
                funcs.update(ext.functions)
            elif ext.name in frame[-1]:
                raise Exception(f"Name clashing! For name {ext.name!r}")
            elif ext.name:
                varproc.rset(frame[-1], ext.name, (temp := {}))
                temp.update(ext.functions)
    frame[-1].update(funcs)
    file = os.path.realpath(file)
    varproc.dependencies["lua"].add(file)


def c_import(frame, file, search_path=None, loc=varproc.meta_attributes["internal"]["main_path"], alias=None):
    if not os.path.isabs(file):
        if search_path is not None:
            file = os.path.join(
                {"_std": info.LINDIR, "_loc": loc}.get(
                    search_path, search_path
                ),
                file,
            )
    if not os.path.isfile(file):
        print("File not found:", file)
        return 1
    result = process_cdef(file, open(file).read())
    if result is None:
        return 1
    name = alias or result["_name"]
    frame[-1][name] = result

def py_import(frame, file, search_path=None, loc=varproc.meta_attributes["internal"]["main_path"], alias=None):
    if not os.path.isabs(file):
        if search_path is not None:
            file = os.path.join(
                {"_std": info.LIBDIR, "_loc": loc}.get(
                    search_path, search_path
                ),
                file,
            )
    if not os.path.exists(file):
        print("Not found:", file)
        return 1
    if os.path.isdir(file):
        if alias:
            frame[-1][alias] = {}
            frame = [frame[-1][alias]]
        if os.path.isfile(files:=os.path.join(file, "include-py.txt")):
            with open(files) as f:
                for line in f.readlines():
                    line = line.strip()
                    if "=>" in line:
                        line, alias = line.split("=>")
                        line = line.strip()
                        alias = alias.strip()
                    else:
                        alias = None
                    if line.startswith("#:"):
                        print(f"{files} [N/A]:",line[2:]) # for messages like deprecation warnings
                    elif line.startswith("#?"):
                        print(line[2:]) # for messages like deprecation warnings
                    elif line.startswith('#') or not line:
                        ...
                    else:
                        if py_import(frame, line, search_path=file, loc=loc):
                            print(f"Something went wrong while importing {line!r}")
                            return 1
            return
        else:
            print(f"python: 'include-py.txt' not found.\nTried to include a directory ({file!r}) without an include file!")
            return 1
    if varproc.is_debug_enabled("show_imports"):
        error.info(f"Imported {file!r}" if not alias else f"Imported {file!r} as {alias}")
    with open(file, "r") as f:
        obj = compile(f.read(), file, "exec")
        try:
            d = {"modules": modules, "dpl": dpl, "__alias__":alias, "frame_stack": frame, "__name__": "__dpl__"}
            exec(obj, d)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            error.error("[N/A]", file, traceback.format_exc())
            return 1
    funcs = {}
    for name, ext in d.items():
        if isinstance(ext, extension):
            if ext.meta_name:
                funcs.update(ext.functions)
            elif ext.name in frame[-1]:
                raise Exception(f"Name clashing! For name {ext.name!r}")
            elif ext.name:
                varproc.rset(frame[-1], ext.name, {})
                for func, value in ext.functions.items():
                    varproc.rset(frame[-1], func, value)
    frame[-1].update(funcs)
    file = os.path.realpath(file)
    varproc.dependencies["python"].add(file)


def call(func, frame, file, args):
    ret = func(frame, file, *args)
    return ret
