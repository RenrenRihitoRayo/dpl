# Parser and Preprocessor
# The heart, the interpreter of DPL

import os
import time
import sys
import itertools
import traceback
import threading
import pickle
import builtins
from copy import deepcopy as copy
from . import arguments as argproc
from . import varproc
from . import info
from . import state
from . import error
from . import utils

IS_STILL_RUNNING = threading.Event()

threads = []

def my_exit(code=0):
    IS_STILL_RUNNING.set()
    raise SystemExit(code)

sys.exit = my_exit
exit = my_exit

O_RSET = varproc.rset
O_RPOP = varproc.rpop

def switch_context_to_unsafe():
    with varproc.W_LOCK:
        varproc.rset = varproc.unsafe_rset
        varproc.rpop = varproc.unsafe_rpop

def switch_context_to_safe():
    with varproc.W_LOCK:
        varproc.rset = O_RSET
        varproc.rpop = O_RPOP

# setup runtime stuff. And yes on import.
try:
    import psutil
    CUR_PROCESS = psutil.Process()
    def get_memory(_, __):
        memory_usage = CUR_PROCESS.memory_info().rss
        return utils.convert_bytes(memory_usage),
    varproc.meta["internal"]["has_get_memory"] = 1
    varproc.meta["internal"]["get_memory"] = get_memory
except ModuleNotFoundError as e:
    varproc.meta["internal"]["has_get_memory"] = 0
    varproc.meta["internal"]["get_memory"] = lambda _, __: (state.bstate("nil"),)

varproc.meta["internal"]["os"] = {
    "uname":info.SYS_MACH_INFO,        # uname
    "architecture":info.SYS_ARCH,      # system architecture (commonly x86 or ARMv7 or whatever arm proc)
    "executable_format":info.EXE_FORM, # name is self explanatory
    "machine":info.SYS_MACH,           # machine information
    "information":info.SYS_INFO,       # basically the tripple
    "processor":info.SYS_PROC,         # processor (intel and such)
    "threads":os.cpu_count()           # physical thread count,
}

varproc.meta["internal"]["libs"] = {
    "core_libs":tuple(map(lambda x: os.path.basename(x), filter(
                os.path.isfile,
                (os.path.join(info.CORE_DIR, f) for f in os.listdir(info.CORE_DIR))
            ))),
    "std_libs":tuple(map(lambda x: os.path.basename(x), filter(
                os.path.isfile,
                (os.path.join(info.LIBDIR, f) for f in os.listdir(info.LIBDIR))
            )))
}

def get_size_of(_, __, object):
    return utils.convert_bytes(sys.getsizeof(object)),

try:
    get_size_of(0)
    varproc.meta["internal"]["sizeof"] = get_size_of
except:
    def temp(_, __, ___):
        return "err:3:Cannot get memory usage of an object!\nIf you are using pypy then please use another interpreter."
    varproc.meta["internal"]["sizeof"] = temp

# Global preprocessing rules
rules = {
    "strict_include":0,
    "automatic_def":1,
    "warnings":1
}

varproc.meta["threading"] = {
    "runtime_event":IS_STILL_RUNNING,
    "is_still_running":lambda _, __: IS_STILL_RUNNING.is_set()
}

# Set of included files.
includes = set()

def rule_enabled(rule):
    "Check if a rule is enabled"
    if rule not in rules:
        error.pre_warn(f"Invalid rule {rule!r}")
        return False
    return bool(rules.get(rule))

def enable_rule(rule):
    "Enable a rule"
    rules[rule] = 1

def disable_rule(rule):
    "Disable a rule"
    if rule not in rules:
        error.pre_warn(f"Invalid rule {rule!r}")
        return
    rules[rule] = 0
    
def get_block(code, current_p, dec={}):
    "Get a code block"
    pos, file, _, _ = code[current_p]
    p = current_p + 1
    k = 1
    res = []
    while p < len(code):
        _, _, ins, _ = code[p]
        if ins in info.INC:
            k += 1
        elif ins in info.DEC or ins in dec:
            k -= 1
        if k == 0:
            break
        else:
            res.append(code[p])
        p += 1
    else:
        print(f"Error in line {pos} file {file!r}\nCause: Block wasnt closed!")
        return None
    return p, res

def process(code, name="__main__"):
    "Preprocess a file"
    res = []
    for lpos, line in filter(lambda x: (
        True if x[1] and not x[1].startswith("#") else False
    ),enumerate(map(str.strip, code.split("\n")), 1)):
        if line.startswith("&"):
            ins, *args = line[1:].lstrip().split()
            argc = len(args)
            if ins == "include" and argc == 1:
                if args[0].startswith("<") and args[0].endswith(">"):
                    file = os.path.join(info.LIBDIR, args[0][1:-1])
                elif args[0].startswith('"') and args[0].endswith('"'):
                    file = os.path.join(os.path.dirname(name), args[0][1:-1])
                    if name != "__main__":
                        file = os.path.join(os.path.dirname(name), file)
                if not os.path.isfile(file):
                    print("File not found:", file)
                    break
                with open(file, "r") as f:
                    res.extend(process(f.read(), name=file))
            elif ins == "set_name" and argc == 1:
                name = str(args[0])
            elif ins == "enable" and argc == 1:
                enable_rule(args[0])
            elif ins == "disable" and argc == 1:
                disable_rule(args[0])
            elif ins == "define" and argc == 0:
                includes.add(name)
            elif ins == "includec" and argc == 1:
                if args[0].startswith("<") and args[0].endswith(">"):
                    file = os.path.join(info.LIBDIR, args[0][1:-1])
                elif args[0].startswith('"') and args[0].endswith('"'):
                    file = os.path.join(os.path.dirname(name), args[0][1:-1])
                    if name != "__main__":
                        file = os.path.join(os.path.dirname(name), file)
                if not os.path.isfile(file):
                    print("File not found:", file)
                    break
                with open(file, "rb") as f:
                    res.extend(pickle.loads(f.read()))
            elif ins == "extend_s" and argc == 1:
                if args[0].startswith("<") and args[0].endswith(">"):
                    file = os.path.join(info.LIBDIR, args[0][1:-1])
                elif args[0].startswith('"') and args[0].endswith('"'):
                    file = os.path.join(os.path.dirname(name), args[0][1:-1])
                    if name != "__main__":
                        file = os.path.join(os.path.dirname(name), file)
                if not os.path.isfile(file):
                    print("File not found:", file)
                    break
                with open(file, "r") as f:
                    res.extend(process(f.read(), name=name))
            else:
                error.pre_error(lpos, name, f"{name!r}-{lpos}:Invalid directive {ins!r}")
                break
        else:
            ins, *args = line.split()
            args = argproc.exprs_preruntime(args)
            res.append((lpos, name, ins, args))
    else:
        return res
    return []

def py_import(frame, file, search_path=None, loc=varproc.meta["internal"]["main_path"]):
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
                "error":error
            }
            exec(obj, d)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            error.error("[N/A]", file, traceback.format_exc())
            exit(2)

def run(code, frame=None):
    "Run code generated by 'process'"
    p = 0
    end_time = start_time = 0
    frame = varproc.new_frame() if frame is None else frame
    while p < len(code) and not IS_STILL_RUNNING.is_set():
        pos, file, ins, args = code[p]
        if ins not in { # Lazy evaluation
            "while",
        }:
            try:
                args = argproc.exprs_runtime(frame, args)
            except Exception as e:
                error.error(pos, file, f"Something went wrong when arguments were processed:\n{e}\n> {args!r}")
                return error.PYTHON_ERROR
        if varproc.is_debug_enabled("show_instructions"):
            error.info(f"Executing: {code[p]}")
        argc = len(args)
        if ins == "fn" and argc >= 1:
            name, *params = args
            temp = get_block(code, p)
            if temp is None:
                break
            else:
                p, body = temp
            varproc.rset(frame[-1], name, {
                "name":name,
                "body":body,
                "args":params,
                "self":state.bstate("nil"),
                "docs":"Function.",
                "defs":{}
            })
        elif ins == "for" and argc == 3 and args[1] == "in":
            name, _, iter = args
            temp = get_block(code, p)
            if temp is None:
                break
            else:
                p, body = temp
            if body:
                for i in iter:
                    varproc.rset(frame[-1], name, i)
                    err = run(body, frame)
                    if err == error.STOP_RESULT:
                        break
                    elif err == error.SKIP_RESULT:
                        continue
                    elif err:
                        return err
        elif ins == "loop" and argc == 0:
            temp = get_block(code, p)
            if temp is None:
                break
            else:
                p, body = temp
            if body:
                while True:
                    err = run(body, frame)
                    if err == error.STOP_RESULT:
                        break
                    elif err == error.SKIP_RESULT:
                        continue
                    elif err:
                        return err
        elif ins == "loop" and argc == 1:
            temp = get_block(code, p)
            if temp is None:
                break
            else:
                p, body = temp
            if body:
                for _ in range(args[0]):
                    err = run(body, frame)
                    if err == error.STOP_RESULT:
                        break
                    elif err == error.SKIP_RESULT:
                        continue
                    elif err:
                        return err
        elif ins == "while" and argc != 0:
            temp = get_block(code, p)
            if temp is None:
                break
            else:
                p, body = temp
            if body:
                while True:
                    try:
                        res, = argproc.exprs_runtime(frame, args)
                        if not res:
                            break
                    except Exception as e:
                        error.error(pos, file, f"Something went wrong when arguments were processed:\n{e}\n> {args!r}")
                        return error.RUNTIME_ERROR
                    err = run(body, frame)
                    if err == error.STOP_RESULT:
                        break
                    elif err == error.SKIP_RESULT:
                        continue
                    elif err:
                        return err
        elif ins == "stop" and argc == 0:
            return error.STOP_RESULT
        elif ins == "skip" and argc == 0:
            return error.SKIP_RESULT
        elif ins == "if" and argc == 1:
            temp = get_block(code, p)
            if temp is None:
                break
            else:
                p, body = temp
            if args[0]:
                err = run(body, frame=frame)
                if err:
                    return err
        elif ins == "if-then" and argc == 1:
            temp = get_block(code, p, {"else"})
            if temp is None:
                break
            else:
                p, true = temp
            temp = get_block(code, p)
            if temp is None:
                break
            else:
                p, false = temp
            if args[0]:
                err = run(true, frame=frame)
                if err:
                    return err
            else:
                err = run(false, frame=frame)
                if err:
                    return err
        elif ins == "set" and argc == 2:
            if varproc.rset(frame[-1], args[0], args[1]):
                error.error(pos, file, "Tried to set a constant variable!\nPlease use fset instead!")
                return error.RUNTIME_ERROR
        elif ins == "const" and argc == 2:
            name = args[0]
            if varproc.rset(frame[-1], name, args[1]):
                error.error(pos, file, "Tried to set a constant variable!\nPlease use fset instead!")
                return error.RUNTIME_ERROR
            consts = varproc.rget(frame[-1], "[const]", default=None)
            if consts:
                consts.append(name if "." not in name else name.rsplit(".", 1)[-1])
            else:
                varproc.rset(frame[-1], "[const]", [name if "." not in name else name.rsplit(".", 1)[-1]], meta=False)
        elif ins == "fset" and argc == 2:
            varproc.rset(frame[-1], args[0], args[1], meta=False)
        elif ins == "del" and argc == 1:
            varproc.rpop(frame[-1], args[0])
            consts = varproc.rget(frame[-1], "[const]", default=None)
            name = args[0] if "." not in args[0] else args[0].rsplit(".", 1)[-1]
            if consts and name in consts:
                consts.remove(name)
        elif ins == "expect" and argc == 1:
            types = args[0]
            temp = get_block(code, p)
            if temp == None:
                break
            else:
                p, body = temp
            OLD_ERROR = error.error
            error.error = lambda *x, **y: None
            err = run(body, frame)
            error.error = OLD_ERROR
            if err == 0:
                if types != "quiet":
                    error.info("Success!")
            elif isinstance(types, str) and types not in {"any", "quiet"} and err not in types:
                print(types)
                return err
            else:
                if types != "quiet":
                    error.info("Error was expected and was not propagated!")
        elif ins == "expect-then" and argc == 1:
            types = args[0]
            temp = get_block(code, p, {"then"})
            if temp == None:
                break
            else:
                p, body = temp

            temp = get_block(code, p)
            if temp == None:
                break
            else:
                p, body2 = temp

            OLD_ERROR = error.error
            error.error = lambda *x, **y: None
            err = run(body, frame)
            error.error = OLD_ERROR
            if err == 0:
                if types != "quiet":
                    error.info("Success!")
            elif isinstance(types, str) and types not in {"any", "quiet"} and err not in types:
                print(types)
                return err
            else:
                if types != "quiet":
                    error.info("Error was expected and was not propagated!")
                err = run(body2, frame)
                if err:
                    error.error(p, file, "An error was captured but then the clause also raised one.")
                    return err
        elif ins == "module" and argc == 1:
            name = args[0]
            temp = [frame[-1]]
            varproc.nscope(temp)
            btemp = get_block(code, p)
            if btemp == None:
                break
            else:
                p, body = btemp
            err = run(body, temp)
            if err:
                return err
            varproc.rset(frame[-1], name, temp[1])
            del temp
        elif ins == "object" and argc == 1:
            varproc.rset(frame[-1], args[0], {
                "_internal":{
                    "name":args[0],
                    "type":"type:"+args[0],
                    "docs":"An object."
                },
                "_im_repr":{ # define a boring default _im_repr
                    "name":0,
                    "args":[],
                    "defs":0,
                    "docs":"Default internal method for repr.",
                    "self":0,
                    "body":[
                        (0, "_internal", "return", (f"<Object {args[0]}>",))
                    ]
                }
            })
        elif ins == "new" and argc == 2:
            obj = varproc.rget(frame[-1], args[0])
            if obj == state.bstate("nil"):
                error.error(pos, file, f"Unknown object {args[0]!r}")
                break
            varproc.rset(obj, "_internal.name", args[1])
            varproc.rset(frame[-1], args[1], copy(obj))
        elif ins == "method" and argc >= 2:
            self, name, *params = args
            if self == state.bstate("nil"):
                error.error(pos, file, "Cannot bind a method to a value that isnt a context!")
                return error.RUNTIME_ERROR
            temp = get_block(code, p)
            if temp is None:
                break
            else:
                p, body = temp
            varproc.rset(self, name, {
                "name":name,
                "body":body,
                "args":params,
                "self":self,
                "docs":f"Method of {varproc.rget(self, '_internal.name')}",
                "defs":{}
            })
        elif ins == "import" and argc == 1:
            if py_import(frame, args[0], varproc.meta["internal"]["lib_path"]):
                return error.IMPORT_ERROR
        elif ins == "import" and argc == 2:
            if py_import(frame, args[0], args[1], loc=os.path.dirname(file)):
                return error.IMPORT_ERROR
        elif ins == "START_TIME" and argc == 0:
            start_time = time.time()
        elif ins == "STOP_TIME" and argc == 0:
            end_time = time.time() - start_time
        elif ins == "LOG_TIME" and argc == 0:
            ct, unit = utils.convert_sec(end_time)
            error.info(f"Elapsed time: {ct:.8f}{unit}")
        elif ins == "cmd" and argc == 1:
            os.system(args[0])
        elif ins == "pass":
            ...
        elif ins == "thread" and argc == 0:
            temp = get_block(code, p)
            if temp is None:
                break
            else:
                p, body = temp
            def th():
                if (err:=run(body, frame)):
                    raise RuntimeError(f"Thread returned an error: {err}")
            th_obj = threading.Thread(target=th)
            threads.append(th_obj)
            th_obj.start()
        elif ins == "exit" and argc == 0:
            my_exit()
        elif ins == "return" and (temp:=varproc.rget(frame[-1], "_returns")) != state.bstate("nil"): # Return to the latched names
            for name, value in zip(temp, args):
                varproc.rset(frame[-1], f"_nonlocal.{name}", value)
            return 0
        elif ins == "help" and argc == 1:
            temp = varproc.rget(frame[-1], f"{args[0]}.docs",
                default=varproc.rget(frame[-1], f"{args[0]}._internal.docs")
            )
            if temp == state.bstate("nil"):
                print(f"\nHelp for {args[0]}: No documentation was found!")
            else:
                print(f"\nHelp for {args[0]}:\n{temp}")
        elif ins == "wait_for_threads" and argc == 0:
            for i in threads:
                i.join()
            threads.clear()
        elif ins == "catch" and argc >= 2: # catch return value of a function
            rets, name, *args = args
            if (temp:=varproc.rget(frame[-1], name)) == state.bstate("nil") or not isinstance(temp, dict):
                error.error(pos, file, f"Invalid function {name!r}!")
                break
            varproc.nscope(frame)
            if temp["defs"]:
                for name, value in itertools.zip_longest(temp["args"], args):
                    if value is None:
                        varproc.rset(frame[-1], name, temp["defs"].get(name, state.bstate("nil")))
                    else:
                        varproc.rset(frame[-1], name, value)
            else:
                if len(args) != len(temp["args"]):
                    error.error(pos, file, f"Function {ins!r} has a parameter mismatch!\nGot {'more' if len(args) > len(temp['args']) else 'less'} than expected.")
                    break
                for name, value in itertools.zip_longest(temp["args"], args):
                    varproc.rset(frame[-1], name, value)
            varproc.rset(frame[-1], "_returns", rets)
            if temp["self"] != state.bstate("nil"):
                varproc.rset(frame[-1], "self", temp["self"])
            err = run(temp["body"], frame)
            if err:
                return err
            varproc.pscope(frame)
        elif ins == "body" and argc >= 1: # give a code block to a python function
            name, *args = args
            if (temp:=varproc.rget(frame[-1], name)) == state.bstate("nil") or not hasattr(temp, "__call__"):
                error.error(pos, file, f"Invalid function {name!r}!")
                break
            try:
                btemp = get_block(code, p)
                if btemp == None:
                    break
                else:
                    p, body = btemp
                if argc == 2 and isinstance(args[0], dict) and args[0].get("[KWARGS]"):
                    args[0].pop("[KWARGS]")
                    pa = args[0].pop("[PARGS]", tuple())
                    res = temp(frame, file, body, *pa, **args[0])
                else:
                    res = temp(frame, file, body, *args)
                if isinstance(res, tuple):
                    for name, value in zip(rets, res):
                        varproc.rset(frame[-1], name, value)
                elif isinstance(res, int) and res:
                    return res
                elif isinstance(res, str):
                    if res == "break":
                        break
                    elif res.startswith("err:"):
                        _, ecode, message = res.split(":", 2)
                        error.error(pos, file, message)
                        return int(ecode)
            except:
                error.error(pos, file, traceback.format_exc()[:-1])
                return error.PYTHON_ERROR
        elif ins == "pycatch" and argc >= 2: # catch return value of a python function
            rets, name, *args = args
            if (temp:=varproc.rget(frame[-1], name)) == state.bstate("nil") or not hasattr(temp, "__call__"):
                error.error(pos, file, f"Invalid function {name!r}!")
                break
            try:
                if argc == 3 and isinstance(args[0], dict) and args[0].get("[KWARGS]"):
                    args[0].pop("[KWARGS]")
                    pa = args[0].pop("[PARGS]", tuple())
                    res = temp(frame, file, *pa, **args[0])
                else:
                    res = temp(frame, file, *args)
                if isinstance(res, tuple):
                    if res is not None:
                        for name, value in zip(rets, res):
                            varproc.rset(frame[-1], name, value)
                elif isinstance(res, int) and res:
                    return res
                elif isinstance(res, str):
                    if res == "break":
                        break
                    elif res.startswith("err:"):
                        _, ecode, message = res.split(":", 2)
                        error.error(pos, file, message)
                        return int(ecode)
            except:
                error.error(pos, file, traceback.format_exc()[:-1])
                return error.PYTHON_ERROR
        elif (temp:=varproc.rget(frame[-1], ins)) != state.bstate("nil") and isinstance(temp, dict): # Call a function
            varproc.nscope(frame)
            if temp["defs"]:
                for name, value in itertools.zip_longest(temp["args"], args):
                    if value is None:
                        varproc.rset(frame[-1], name, temp["defs"].get(name, state.bstate("nil")))
                    else:
                        varproc.rset(frame[-1], name, value)
            else:
                if len(args) != len(temp["args"]):
                    error.error(pos, file, f"Function {ins!r} has a parameter mismatch!\nGot {'more' if len(args) > len(temp['args']) else 'less'} than expected.")
                    break
                for name, value in itertools.zip_longest(temp["args"], args):
                    varproc.rset(frame[-1], name, value)
            if temp["self"] != state.bstate("nil"):
                varproc.rset(frame[-1], "self", temp["self"])
            err = run(temp["body"], frame)
            if err:
                return err
            varproc.pscope(frame)
        elif (temp:=varproc.rget(frame[-1], ins)) != state.bstate("nil") and hasattr(temp, "__call__"): # call a python function
            try:
                if argc == 1 and isinstance(args[0], dict) and args[0].get("[KWARGS]"):
                    args[0].pop("[KWARGS]")
                    pa = args[0].pop("[PARGS]", tuple())
                    res = temp(frame, file, *pa, **args[0])
                else:
                    res = temp(frame, file, *args)
                if isinstance(res, int) and res:
                    return res
                elif isinstance(res, str):
                    if res == "break":
                        break
                    elif res.startswith("err:"):
                        _, ecode, message = res.split(":", 2)
                        error.error(pos, file, message)
                        return int(ecode)
            except:
                error.error(pos, file, traceback.format_exc()[:-1])
                return error.PYTHON_ERROR
        else:
            error.error(pos, file, f"Invalid instruction {ins}")
            return error.RUNTIME_ERROR
        p += 1
    else:
        return 0
    error.error(pos, file, "Error was raised!")
    return error.SYNTAX_ERROR
