# Parser and Preprocessor
# The heart, the interpreter of DPL

import os
import time
import sys
import itertools
import traceback
import threading
import pickle
from copy import deepcopy as copy
from . import arguments as argproc
from . import varproc
from . import info
from . import state
from . import error
from . import utils

IS_STILL_RUNNING = threading.Event()

def my_exit():
    IS_STILL_RUNNING.set()
    exit()

try:
    import resource
    def get_memory(_, __):
        memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return utils.convert_bytes(memory_usage),
    varproc.meta["internal"]["has_get_memory"] = 1
    varproc.meta["internal"]["get_memory"] = get_memory
except ModuleNotFoundError:
    varproc.meta["internal"]["has_get_memory"] = 0
    varproc.meta["internal"]["get_memory"] = lambda f, ff: ((0, "Not available!"),)

# Global preprocessing rules
rules = {
    "strict_include":0,
    "automatic_def":1,
    "warnings":1
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
                if not os.path.isfile(file):
                    print("File not found:", file)
                    break
                with open(file, "r") as f:
                    res.extend(process(f.read(), name=file))
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
                if not os.path.isfile(file):
                    print("File not found:", file)
                    break
                with open(file, "rb") as f:
                    res.extend(pickle.loads(f.read()))
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

def py_import(frame, file, search_path=None):
    if search_path is not None:
        file = os.path.join({
            "@lib":varproc.meta["internal"]["lib_path"]
        }.get(search_path, search_path), file)
    if not os.path.isfile(file):
        print("File not found:", file)
        return 1
    if varproc.is_debug_enabled("show_imports"):
        error.info(f"Imported {file!r}")
    with open(file, "r") as f:
        obj = compile(f.read(), file, "exec")
        def add_func(frame=frame[-1]):
            def wrap(x):
                varproc.rset(frame, getattr(x, "__name__", "_temp.dump"), x)
                return x
            return wrap
        try:
            d = {
                "add_func":add_func,
                "varproc":varproc,
                "frame":frame,
                "run":run,
                "process":process,
                "os":os,
                "info":info,
                "__name__":"__dpl__",
                "__path__":os.path.dirname(file),
                "print":error.info,
                "raw_print":print
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
                raise
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
                "_internal":{
                    "name":name,
                    "type":"type:function"
                },
                "name":name,
                "body":body,
                "args":params,
                "self":state.bstate("nil"),
                "defs":{}
            })
        elif ins == "raw_println":
            print(*args)
        elif ins == "raw_print":
            print(*args, end='')
        elif ins == "raw_term_print":
            s = ""
            for i in args:
                if isinstance(i, int):
                    s += chr(i)
                elif isinstance(i, str):
                    s += i
                else:
                    s += repr(i)
            sys.stdout.write(s)
            sys.stdout.flush()
        elif ins == "println":
            for item in args:
                if isinstance(item, dict) and "_internal" in item and "_im_repr" in item:
                    varproc.nscope(frame)
                    varproc.nscope(frame)
                    varproc.rset(frame[-1], "self", item)
                    varproc.rset(frame[-1], "_returns", ("repr",))
                    err = run(item["_im_repr"]["body"], frame)
                    if err:
                        return err
                    varproc.pscope(frame)
                    repr = frame[-1].get("repr", state.bstate("nil"))
                    varproc.pscope(frame)
                    print(repr, end=' ' if item != args[-1] else '')
                else:
                    print(item, end=' ' if item != args[-1] else '')
            print()
        elif ins == "print":
            for item in args:
                if isinstance(item, dict) and "_internal" in item and "_im_repr" in item:
                    varproc.nscope(frame)
                    varproc.nscope(frame)
                    varproc.rset(frame[-1], "self", item)
                    varproc.rset(frame[-1], "_returns", ("repr",))
                    err = run(item["_im_repr"]["body"], frame)
                    if err:
                        return err
                    varproc.pscope(frame)
                    repr = frame[-1].get("repr", state.bstate("nil"))
                    varproc.pscope(frame)
                    print(repr, end=' ' if item != args[-1] else '')
                else:
                    print(item, end=' ' if item != args[-1] else '')
        elif ins == "input" and argc == 1:
            varproc.rset(frame[-1], args[0], input())
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
                    if err == -1:
                        break
                    elif err == -2:
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
                    if err == -1:
                        break
                    elif err == -2:
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
                    if err == -1:
                        break
                    elif err == -2:
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
                        return 1
                    err = run(body, frame)
                    if err == -1:
                        break
                    elif err == -2:
                        continue
                    elif err:
                        return err
        elif ins == "stop" and argc == 0:
            return -1
        elif ins == "skip" and argc == 0:
            return -2
        elif ins == "if" and argc == 1:
            temp = get_block(code, p)
            if temp is None:
                break
            else:
                p, body = temp
            if args[0]:
                err = run(body, frame=frame)
                if err != 0:
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
                if err != 0:
                    return err
            else:
                err = run(false, frame=frame)
                if err != 0:
                    return err
        elif ins == "set" and argc == 2:
            varproc.rset(frame[-1], args[0], args[1])
        elif ins == "method" and argc >= 2:
            self, name, *params = args
            temp = get_block(code, p)
            if temp is None:
                break
            else:
                p, body = temp
            varproc.rset(self, name, {
                "_internal":{
                    "name":name,
                    "type":"type:function,method"
                },
                "name":name,
                "body":body,
                "args":params,
                "self":self,
                "defs":{}
            })
        elif ins == "object" and argc == 1:
            varproc.rset(frame[-1], args[0], {
                "_internal":{
                    "name":args[0],
                    "type":"type:"+args[0]
                }
            })
        elif ins == "new" and argc == 2:
            obj = varproc.rget(frame[-1], args[0])
            if obj == state.bstate("nil"):
                error.error(pos, file, f"Unknown object {args[0]!r}")
                break
            varproc.rset(obj, "_internal.name", args[1])
            varproc.rset(frame[-1], args[1], obj)
        elif ins == "import" and argc == 1:
            if py_import(frame, args[0], varproc.meta["internal"]["lib_path"]):
                return 3
        elif ins == "import" and argc == 2:
            if py_import(frame, args[0], args[1]):
                return 3
        elif ins == "START_TIME" and argc == 0:
            start_time = time.time()
        elif ins == "STOP_TIME" and argc == 0:
            end_time = time.time() - start_time
        elif ins == "LOG_TIME" and argc == 0:
            ct, unit = utils.convert_sec(end_time)
            error.info(f"Elapsed time: {ct:.8f}{unit}")
        elif ins == "panic" and argc <= 1:
            if argc:
                error.error(pos, file, args[0])
            return 4
        elif ins == "cmd" and argc == 1:
            os.system(args[0])
        elif ins == "pass":
            ...
        elif (temp:=varproc.rget(frame[-1], ins)) != state.bstate("nil") and hasattr(temp, "__call__"):
            try:
                temp(frame, file, *args)
            except:
                error.error(pos, file, traceback.format_exc())
                break
        elif ins == "thread" and argc == 0:
            temp = get_block(code, p)
            if temp is None:
                break
            else:
                p, body = temp
            def th():
                if (err:=run(body, frame)):
                    return err
            th_obj = threading.Thread(target=th)
            th_obj.start()
        elif ins == "exit" and argc == 0:
            my_exit()
        elif ins == "pycatch" and argc >= 2:
            rets, name, *args = args
            if (temp:=varproc.rget(frame[-1], name)) == state.bstate("nil") or not hasattr(temp, "__call__"):
                error.error(p, file, f"Invalid function {name!r}!")
                break
            try:
                res = temp(frame, file, *args)
                for name, value in zip(rets, res):
                    varproc.rset(frame[-1], name, value)
            except:
                error.error(pos, file, traceback.format_exc())
                break
        elif ins == "return" and (temp:=varproc.rget(frame[-1], "_returns")) != state.bstate("nil"): # Return to the latched names
            for name, value in zip(temp, args):
                varproc.rset(frame[-1], f"_nonlocal.{name}", value)
            return 0
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
        elif ins == "catch" and argc >= 2:
            rets, name, *args = args
            if (temp:=varproc.rget(frame[-1], name)) == state.bstate("nil") or not isinstance(temp, dict):
                error.error(pos, file, f"Invalid function {name!r}!")
                break
            varproc.nscope(frame)
            for name, value in zip(temp["args"], args):
                varproc.rset(frame[-1], name, value)
            varproc.rset(frame[-1], "_returns", rets)
            if temp["self"] != state.bstate("nil"):
                varproc.rset(frame[-1], "self", temp["self"])
            err = run(temp["body"], frame)
            if err:
                return err
            varproc.pscope(frame)
        else:
            error.error(pos, file, f"Invalid instruction {ins}")
            return 2
        p += 1
    else:
        return 0
    error.error(pos, file, "Error was raised!")
    return 1