# A module to help the parser call dynamically loaded functions and to load them too
# This is needed for the cythonized parser and slows down the pure python impl!
# I tried it, it still failed :))

from . import utils
from . import varproc
from . import arguments as argproc
from . import info
from . import error
from . import state
from . import restricted
import time
import os, sys
import traceback

run = None
process = None

def register_run(func):
    global run
    run = func

def register_process(func):
    global process
    process = func

def py_import(frame, file, search_path=None, loc=varproc.meta["internal"]["main_path"]):
    if not os.path.isabs(file):
        if search_path is not None:
            file = os.path.join({
                "@lib":varproc.meta["internal"]["lib_path"],
                "@loc":loc
            }.get(search_path, search_path), file)
        if not os.path.isfile(file):
            print("File not found:", file)
            return 1
    if varproc.is_debug_enabled("show_imports"):
        error.info(f"Imported {file!r}")
    with open(file, "r") as f:
        obj = compile(f.read(), file, "exec")
        def add_func(name=None, frame=frame[-1]):
            def wrap(x):
                if name is None:
                    fname = getattr(x, "__name__", "_dump")
                else:
                    fname = name
                varproc.rset(frame, fname, x)
                return x
            return wrap
        try:
            d = {
                "add_func":add_func,
                "varproc":varproc,
                "frame":frame,
                "run_code":run,
                "process_code":process,
                "os":os,
                "sys":sys,
                "info":info,
                "__name__":"__dpl__",
                "__path__":os.path.dirname(file),
                "print":error.info,
                "state":state,
                "logging":error,
                "raw_print":print,
                "_import":py_import,
                "argproc":argproc,
                "add_method":argproc.add_method,
                "error":error,
                "__import__":__import__
            }
            exec(obj, d)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            error.error("[N/A]", file, traceback.format_exc())
            return 1

def py_import_string(frame, file_name, code, search_path=None, loc=varproc.meta["internal"]["main_path"]):
    if not os.path.isabs(file_name):
        if search_path is not None:
            file = os.path.join({
                "@lib":varproc.meta["internal"]["lib_path"],
                "@loc":loc
            }.get(search_path, search_path), file_file)
        if not os.path.isfile(file_name):
            print("File not found:", file_file)
            return 1
    if varproc.is_debug_enabled("show_imports"):
        error.info(f"Imported {file_name!r}")
    obj = compile(code, file_name, "exec")
    def add_func(name=None, frame=frame[-1]):
        def wrap(x):
            if name is None:
                fname = getattr(x, "__name__", "_dump")
            else:
                fname = name
            varproc.rset(frame, fname, x)
            return x
        return wrap
    try:
        d = {
            "add_func":add_func,
            "varproc":varproc,
            "frame":frame,
            "run_code":run,
            "process_code":process,
            "os":os,
            "sys":sys,
            "info":info,
            "__path__":os.path.dirname(file_name),
            "print":error.info,
            "state":state,
            "logging":error,
            "raw_print":print,
            "_import":py_import,
            "argproc":argproc,
            "add_method":argproc.add_method,
            "error":error
        }
        d.update(restricted.restricted_builtins)
        d["__name__"] = "__dpl__"
        exec(obj, d)
    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        error.error("[N/A]", file_name, traceback.format_exc())
        return 1

def call(func, frame, file, args, kwargs={}):
    if varproc.is_debug_enabled("track_time"):
        start = time.time()
    ret = func(frame, file, *args, **kwargs)
    if varproc.is_debug_enabled("track_time"):
        delta = time.time() - start
        if delta > varproc.get_debug("time_threshold"):
            delta_value, delta_unit = utils.convert_sec(delta)
            error.info(f"The function {func} took too long!\nPrecisely: {delta_value:,.8f}{delta_unit}")
    return ret

def call_w_body(func, frame, file, body, args, kwargs={}):
    if varproc.is_debug_enabled("track_time"):
        start = time.time()
    ret = func(frame, file, body, *args, **kwargs)
    if varproc.is_debug_enabled("track_time"):
        delta = time.time() - start
        if delta > varproc.get_debug("time_threshold"):
            delta_value, delta_unit = utils.convert_sec(delta)
            error.info(f"The function {func} took too long!\nPrecisely: {delta_value:,.8f}{delta_unit}")
    return ret