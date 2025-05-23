# A module to help the parser call dynamically loaded functions and to load them too
# This is needed for the cythonized parser and slows down the pure python impl!
# I tried it, it still failed :)

import itertools
import time
import os, sys
import traceback
from . import type_checker
from . import utils
from . import varproc
from . import arguments as argproc
from . import info
if "no-lupa" not in info.program_flags:
    import lupa
from types import ModuleType
from . import error
from . import state
from . import restricted
from . import objects
from . import constants
from . import py_argument_handler
arguments_handler = py_argument_handler.arguments_handler


def register_run(func):
    dpl.run_code = func


def register_process(func):
    dpl.process_code = func


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
        self.__meth = {}  # methods
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
            if typed:
                type_checker.register(typed.replace("$$", self.mangle(name)))
            return func
        return wrap

    def add_method(self, name=None, from_func=False):
        "Add a method."
        def wrap(func):
            nonlocal name
            if name is None:
                name = getattr(func, "__name__", None) or "_"
            self.__meth[self.mangle(name)] = (
                func if not from_func else lambda *args: func(args[0], None, *args[1:])
            )
            return func
        return wrap

    def get(self, name, default=None):
        return self.__data.get(name, default)

    def mangle(self, name):
        return (
            f"{self._name}.{name}"
            if not self.meta_name
            else f"{self.meta_name}:{name}"
        )

    @property
    def name(self):
        return (self._name
            if not self.meta_name
            else self.meta_name)

    @property
    def functions(self):
        return self.__func

    @property
    def methods(self):
        return self.__meth

    @property
    def items(self):
        return self.__data

    def __repr__(self):
        return f"Extension<{self._name or f'{self.meta_name}:*'!r}>"


def require(path):
    "Import a python file in the lib dir.\nIn cases of 'dir/.../file' use ['dir', ..., 'file'],\nthis uses os.path.join to increase portability."
    mod = {
        "__name__": "__dpl_require__",
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

    def pycall(func, args, table):
        return func(*(args or []), **table)
    
    def add_matcher(name):
        def wrap(fn):
            argproc.matches[name] = fn
            return fn
        return wrap

    type_checker = type_checker


def get_py_params(func):
    if not hasattr(func, "__code__"):
        return None
    co = func.__code__
    arg_count = co.co_argcount
    return co.co_varnames[:arg_count]

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
            if ext.name in frame[-1]:
                raise Exception(f"Name clashing! For name {ext.name!r}")
            if ext.name:
                varproc.rset(frame[-1], ext.name, (temp := {}))
                temp.update(ext.functions)
            else:
                funcs.update(ext.functions)
            meths.update(ext.methods)
    frame[-1].update(funcs)
    argproc.methods.update(meths)
    file = os.path.realpath(file)
    if search_path in varproc.dependencies["lua"]:
        varproc.dependencies["lua"][search_path].add(file)
    else:
        varproc.dependencies["lua"][search_path] = {file}


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
            d = {"__name__": "__dpl__", "modules": modules, "dpl": dpl, "__alias__":alias}
            exec(obj, d)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            error.error("[N/A]", file, traceback.format_exc())
            return 1
    funcs = {}
    meths = {}
    for name, ext in d.items():
        if isinstance(ext, extension):
            if ext.meta_name:
                funcs.update(ext.functions)
            elif ext.name in frame[-1]:
                raise Exception(f"Name clashing! For name {ext.name!r}")
            elif ext.name:
                varproc.rset(frame[-1], ext.name, (temp := {}))
                temp.update(ext.functions)
            meths.update(ext.methods)
    frame[-1].update(funcs)
    argproc.methods.update(meths)
    file = os.path.realpath(file)
    if search_path in varproc.dependencies["python"]:
        varproc.dependencies["python"][search_path].add(file)
    else:
        varproc.dependencies["python"][search_path] = {file}


def call(func, frame, file, args):
    if args and isinstance(args[0], arguments_handler):
        if args[0].args:
            args[0].args.insert(0, file)
            args[0].args.insert(0, frame)
        else:
            args[0].args = [frame, file]
        ret = args[0].call(func)
    else:
        ret = func(frame, file, *args)
    return ret