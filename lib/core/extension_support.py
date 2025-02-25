# A module to help the parser call dynamically loaded functions and to load them too
# This is needed for the cythonized parser and slows down the pure python impl!
# I tried it, it still failed :)

from . import utils
from . import varproc
from . import arguments as argproc
from . import info
from . import error
from . import state
from . import restricted
from . import objects
import types
import itertools
import time
import os, sys
import traceback
import __main__


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
    types = types
    itertools = itertools


class extension:
    "A class to help define methods and functions."

    def __init__(self, name=None, meta_name=None):
        self.__func = {}  # functions
        self.__meth = {}  # methods
        self.name = (
            name  # This is a scope name,              dpl defined name.func_name
        )
        self.meta_name = meta_name  # while this is the mangled name, python defined "{meta_name}:{func_name}"

    def add_func(self, name=None):
        "Add a function."

        def wrap(func):
            nonlocal name
            if func.__doc__ is None:
                func.__doc__ = (
                    f"Function {self.meta_name}:{name}"
                    if self.meta_name
                    else f"{self.name}.{name}"
                ) + ": Default doc string..."
            if name is None:
                name = getattr(func, "__name__", None) or "_"
            self.__func[name if not self.meta_name else f"{self.meta_name}:{name}"] = (
                func
            )
            return func

        return wrap

    def add_method(self, name=None, process=True, from_func=False):
        "Add a method."

        def wrap(func):
            nonlocal name
            if name is None:
                name = getattr(func, "__name__", None) or "_"
            self.__meth[
                (
                    f"{self.name}.{name}"
                    if not self.meta_name
                    else f"{self.meta_name}:{name}"
                )
            ] = process, (
                func
                if not from_func
                else lambda *args: func(args[0], None, *args[1:])[0]
            )
            return func

        return wrap

    def __setitem__(self, name, value):
        self.__func[name if not self.meta_name else f"{self.meta_name}:{name}"] = value

    def __getitem__(self, name):
        return self.__func[name if not self.meta_name else f"{self.meta_name}:{name}"]

    def get(self, name, default=None):
        return self.__data.get(name, default)

    @property
    def functions(self):
        return self.__func

    @property
    def methods(self):
        return self.__meth


def require(path):
    "Import a python in the lib dir.\nIn cases of 'dir/.../file' use ['dir', ..., 'file'],\nthis uses os.path.join to increase portability."
    mod = {
        "__name__": "__dpl_require__",
        "modules": modules,
        "dpl": dpl,
        "__import__": restricted.restricted(__import__),
    }
    if isinstance(path, (list, tuple)):
        path = os.path.join(*path)
    try:
        with open(os.path.join(info.LIBDIR, path), "r") as f:
            exec(compile(f.read(), path, "exec"), mod)
        r = types.ModuleType(path)
        for name, value in mod.items():
            setattr(r, name, value)
        return r
    except:
        return None


class dpl:
    require = require
    utils = utils
    varproc = varproc
    arguments = argproc
    info = info
    error = error
    state = state
    restricted = restricted
    state_nil = state.bstate("nil")
    state_none = state.bstate("none")
    state_true = 1
    state_false = 0
    extension = extension
    objects = objects
    falsy = (state_nil, state_none, state_false, None, False)
    truthy = (state_true, True)


def py_import(frame, file, search_path=None, loc=varproc.meta["internal"]["main_path"]):
    if not os.path.isabs(file):
        if search_path is not None:
            file = os.path.join(
                {"_std": varproc.meta["internal"]["lib_path"], "_loc": loc}.get(
                    search_path, search_path
                ),
                file,
            )
        if not os.path.isfile(file):
            print("File not found:", file)
            return 1
    if varproc.is_debug_enabled("show_imports"):
        error.info(f"Imported {file!r}")
    with open(file, "r") as f:
        obj = compile(f.read(), file, "exec")
        try:
            d = {"__name__": "__dpl__", "modules": modules, "dpl": dpl}
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
    if search_path in varproc.meta["dependencies"]["python"]:
        varproc.dependencies["python"][search_path].add(file)
    else:
        varproc.dependencies["python"][search_path] = {file}


def py_import_string(
    frame, file_name, code, search_path=None, loc=varproc.meta["internal"]["main_path"]
):
    if not os.path.isabs(file_name):
        if search_path is not None:
            file = os.path.join(
                {"@lib": varproc.meta["internal"]["lib_path"], "@loc": loc}.get(
                    search_path, search_path
                ),
                file_file,
            )
        if not os.path.isfile(file_name):
            print("File not found:", file_file)
            return 1
    if varproc.is_debug_enabled("show_imports"):
        error.info(f"Imported {file_name!r}")
    obj = compile(code, file_name, "exec")
    try:
        d = {"modules": modules, "dpl": dpl}
        d["__name__"] = "__dpl__"
        exec(obj, d)
    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        error.error("[N/A]", file_name, traceback.format_exc())
        return 1
    funcs = {}
    meths = {}
    for name, ext in d.items():
        if isinstance(ext, extension):
            if ext.name in frame[-1]:
                raise Exception(f"Name clashing! For name {ext.name!r}")
            funcs.update(ext.functions)
            meths.update(ext.methods)
    frame[-1].update(funcs)
    argproc.methods.update(meths)


def call(func, frame, file, args, kwargs={}):
    if varproc.is_debug_enabled("track_time"):
        start = time.time()
    ret = func(frame, file, *args, **kwargs)
    if varproc.is_debug_enabled("track_time"):
        delta = time.time() - start
        if delta > varproc.get_debug("time_threshold"):
            delta_value, delta_unit = utils.convert_sec(delta)
            error.info(
                f"The function {func} took too long!\nPrecisely: {delta_value:,.8f}{delta_unit}"
            )
    return ret


def call_w_body(func, frame, file, body, args, kwargs={}):
    if varproc.is_debug_enabled("track_time"):
        start = time.time()
    ret = func(frame, file, body, *args, **kwargs)
    if varproc.is_debug_enabled("track_time"):
        delta = time.time() - start
        if delta > varproc.get_debug("time_threshold"):
            delta_value, delta_unit = utils.convert_sec(delta)
            error.info(
                f"The function {func} took too long!\nPrecisely: {delta_value:,.8f}{delta_unit}"
            )
    return ret
