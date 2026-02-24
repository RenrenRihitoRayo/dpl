# Parser and Preprocessor
# The heart, the interpreter of DPL
# will coexist beside py_parser2 cuz why not
# makes sure HLIR can still be executed
# directly

import time
import itertools
from copy import deepcopy
from . import py_argument_handler
from .runtime import *
from . import utils
from . import objects
from . import constants
import threading
import traceback
import sys
import os
import inspect
from .info import PERM_LIBDIR, INC_TERMINAL, get_path_with_lib, INC_EXT, ARGV
from .varproc import preprocessing_flags
from . import varproc
arguments_handler = py_argument_handler.arguments_handler

start_time = end_time = 0

def copy(obj, memo=None):
    if memo is None:
        memo = {}
    obj_id = id(obj)
    if obj_id in memo:
        return memo[obj_id]
    if isinstance(obj, dict):
        dup = type(obj)()
        memo[obj_id] = dup
        dup.update({k: copy(v, memo) for k, v in obj.items()})
        return dup
    elif isinstance(obj, list):
        dup = type(obj)()
        memo[obj_id] = dup
        dup.extend(copy(v, memo) for v in obj)
        return dup
    elif isinstance(obj, set):
        dup = set()
        memo[obj_id] = dup
        dup.update(copy(v, memo) for v in obj)
        return dup
    elif isinstance(obj, tuple):
        dup = tuple(copy(v, memo) for v in obj)
        memo[obj_id] = dup
        return dup
    else:
        try:
            dup = deepcopy(obj, memo)
            memo[obj_id] = dup
            return dup
        except Exception:
            # Fallback: keep shallow reference
            memo[obj_id] = obj
            return obj

process_hlir = None
empty_bod = []

def register_execute(func):
    global pp2_execute
    pp2_execute = func

def register_process_hlir(func):
    global process_hlir
    process_hlir = func

def get_block(code, current_p, supress=False, start=1):
    "Get a code block. Runtime! (helps init become faster)"
    instruction_pointer = current_p + 1
    line_position, file, ins, _, _ = code[instruction_pointer]
    k = start
    if k == 0 and ins not in INCREAMENTS:
        error.error(line_position, file, "Expected to have started with an instruction that indents.")
        return None
    res = []
    while instruction_pointer < len(code):
        _, _, ins, _, _ = code[instruction_pointer]
        if ins in INC_EXT:
            k += 1
        elif ins == "end":
            k -= 1
        if k == 0:
            break
        instruction_pointer += 1
    else:
        if not supress:
            print(f"Error in line {line_position} file {file!r}\nCause: Block wasnt closed!")
        return None
    return instruction_pointer, code[current_p+(2-start):instruction_pointer]


def pprint(d, l=0, seen=None, hide=True):
    "Custom pretty printer"
    if seen is None:
        seen = set()
    if id(d) in seen:
        print("  "*l+"...")
        return
    seen.add(id(d))
    if isinstance(d, function_type):
        print(("  "*l+repr(d))+",")
        return
    elif isinstance(d, list | tuple):
        for i in d:
            if isinstance(i, list):
                print("  "*l+"list")
                pprint(i, l+1, seen)
                print("  "*l+"end")
            elif isinstance(i, tuple):
                print("  "*l+"tuple")
                pprint(i, l+1, seen)
                print("  "*l+"end")
            elif isinstance(i, object_type):
                print("  "*l+f"dict # {i['_type_name']}")
                pprint(i, l+1, seen)
                print("  "*l+"end")
            elif isinstance(i, dict):
                print("  "*l+"dict")
                pprint(i, l+1, seen)
                print("  "*l+"end")
            elif callable(i):
                print("  "*l+f"... # {i!r}")
            elif isinstance(i, bool):
                print("  "*l+f". {'true' if i else 'false'}")
            elif isinstance(i, ID):
                if i.read == "norm": r = ":"
                elif i.read == "spec": r = "?:"
                else: r = ""
                print("  "*l+f". {r}{i.name}")
            elif not isinstance(i, str | int | float):
                print("  "*l+f"... # {i!r}")
            else:
                print("  "*l+f". {i!r}")
        return
    elif not isinstance(d, dict):
        return
    else:
        for name, value in d.items():
            if isinstance(name, str) and name.startswith("_") and hide:
                ...
            elif isinstance(value, function_type):
                print("  "*l+f"set {value['name']} = ... # {value!r}")
                continue # as of now just print the function normally
                print("  "*l+f"dict {name!r} # {value}")
                pprint(dict(value), l+1, seen)
                print("  "*l+"end")
            elif isinstance(value, object_type):
                print("  "*l+f"dict {name!r} # {value['_type_name']}")
                pprint(value, l+1, seen)
                print("  "*l+"end")
            elif isinstance(value, dict):
                print("  "*l+f"dict {name!r}")
                pprint(value, l+1, seen)
                print("  "*l+"end")
            elif isinstance(value, list):
                print("  "*l+f"list {name!r}")
                pprint(value, l+1, seen)
                print("  "*l+"end")
            elif isinstance(value, tuple):
                print("  "*l+f"tuple {name!r}")
                pprint(value, l+1, seen)
                print("  "*l+"end")
            elif callable(value):
                print("  "*l+f"set {name!r} = ... # {value!r}")
            elif isinstance(value, bool):
                print("  "*l+f"set {name!r} = {'true' if value else 'false'}")
            elif isinstance(value, ID):
                if value.read == "norm": r = ":"
                elif value.read == "spec": r = "?:"
                else: r = ""
                print("  "*l+f"set {name!r} = {r}{value.name}")
            elif not isinstance(value, str | int | float):
                print("  "*l+f"set {name!r} = ... # {value!r}")
            else:
                print("  "*l+f"set {name!r} = {value!r}")


def recursive_replace(data, target, replacement):
    if isinstance(data, (str, bytes)):
        return replacement if data == target else data
    elif isinstance(data, Expression):
        return Expression(recursive_replace(item, target, replacement) for item in data)
    elif isinstance(data, list):
        return [recursive_replace(item, target, replacement) for item in data]
    elif isinstance(data, tuple):
        return tuple(recursive_replace(item, target, replacement) for item in data)
    elif isinstance(data, set):
        return {recursive_replace(item, target, replacement) for item in data}
    else:
        return replacement if data == target else data


def process_inline(args, inline_fn):
    res = []
    params, body = inline_fn["args"], inline_fn["body"]
    values = tuple(zip(params, args))
    for [line_pos, module_name, ins, m, args] in body:
        nargs = args
        for name, value in values:
            current_name = f"::{name}"
            ins, nargs = recursive_replace([ins, nargs], current_name, value)
        res.append((line_pos, module_name, ins, m, to_static(nargs) if varproc.meta_attributes["preprocessing_flags"]["EXPRESSION_FOLDING"] else nargs))
    return res

def process_blocks(frame, code):
    pos = 0
    res = []
    while pos < len(code):
        entire_line = [lpos, fpos, ins, body, args] = code[pos]
        argc = len(args)
        if args and preprocessing_flags["EXPRESSION_FOLDING"]:
            entire_line = list(entire_line)
            try:
                args = to_static(args, env=frame)
                entire_line[4] = args
            except Exception as e:
                error.error(lpos, fpos, traceback.format_exc() + "to_static couldnt process")
                exit(error.PREPROCESSING_ERROR)
            entire_line = tuple(entire_line)

        if ins == "set::static" and argc == 3 and args[1] == "=":
            name, _, value = process_args(frame[-1], args)
            rset(frame[-1], name, value)
            pos += 1
            continue
        
        if ins == "set" and argc == 3 and args[1] == "=":
            name = process_arg(frame[-1], args[0])
            if rget(frame[-1], name, default=None) is not None:
                rpop(frame[-1], name)

        if ins in INC_TERMINAL:
            if body is not None:
                res.append((lpos, fpos, ins, process_blocks(frame, body), args))
            else:
                res.append(entire_line)
            break
        if ins in INC_EXT and not body:
            temp = get_block(code, pos)
            if temp is None:
                error.error(lpos, fpos, f"{ins} statement isnt closed!")
                exit(error.PREPROCESSING_ERROR)
            pos, block = temp
            if (not block) and ins in ("for", "loop", "fn") and \
            preprocessing_flags["DEAD_CODE_ELLIMIMATION"]:
                error.warning(lpos, fpos, f"{ins} statement is empty!")
                if ins == "for":
                    if not preprocessing_flags["FOR_LOOP_SUBSTITUTION"]:
                        error.warning(lpos, fpos, f"variable {args[0]} would not be defined!")
                    else:
                        if isinstance(args[2], list | tuple):
                            last = args[2][-1]
                        elif isinstance(args[2], range):
                            last = args[2].start + ((args[2].stop - 1 - args[2].start) // args[2].step) * args[2].step
                        else:
                            print(args[2])
                            error.warning(lpos, fpos, f"variable {args[0]} would not be defined!\nFor loop substitution failed!")
                            pos += 1
                            continue
                        res.append((lpos, fpos, "set", None, [args[0], "=", last]))
                elif ins == "fn":
                    error.warning(lpos, fpos, f"function {args[0]} would not be defined!")

            if block and ins in ("for", "loop", "fn") and block[0][2] in INC_TERMINAL and \
            preprocessing_flags["DEAD_CODE_ELLIMIMATION"]:
                if ins == "fn" and block[-1][2] == "return" and block[-1][4]:
                    if is_static(block[-1][4]):
                        error.warning(lpos, fpos, f"In function {args[0]}, a constant wrapped by a function is not good practice. Use variables instead. In the future this will be an error.")
                    res.append((lpos, fpos, ins, process_blocks(frame, block), args))
                    pos += 1
                    continue

                error.warning(lpos, fpos, f"{ins} statement is empty!")
                if ins == "for":
                    if not preprocessing_flags["FOR_LOOP_SUBSTITUTION"]:
                        error.warning(lpos, fpos, f"variable {args[0]} would not be defined!")
                    else:
                        if isinstance(args[2], list | tuple):
                            last = args[2][-1]
                        elif isinstance(args[2], range):
                            last = args[2].start + ((args[2].stop - 1 - args[2].start) // args[2].step) * args[2].step
                        else:
                            print(args[2])
                            error.warning(lpos, fpos, f"variable {args[0]} would not be defined!\nFor loop substitution failed!")
                            pos += 1
                            continue
                        res.append((lpos, fpos, "set", None, [args[0], "=", last]))
                elif ins == "fn":
                    error.warning(lpos, fpos, f"function {args[0]} would not be defined!")
            else:
                res.append((lpos, fpos, ins, process_blocks(frame, block), args))
        else:
            res.append(entire_line)
        pos += 1
    return res


def process_code(fcode, name="__main__"):
    """
    Preprocess a file. Output can then be ran by the run function.
    The code this returns is called HLIR or high level ir, since
    it can be easily reconstructed back to the source.
    Wanna see the dump of a script?
    Do "dpl.py dump-hlir file.dpl" the file will be saved
    in `file.dpl.hlir`, this is just a dump and to actually
    make it executable use `dpl.py compile file.dpl` saves it
    to `file.cdpl` and run with `rc`
    """
    res = []
    nframe = new_frame()
    multiline = False
    last_comment = 0
    fcode = fcode.replace("!::__file__", name)
    for lpos, line in filter(
        lambda x: (
            True
            if x[1] and not x[1].startswith("#") and not x[1].startswith("...")
            else False
        ),
        enumerate(map(str.strip, fcode.split("\n")), 1),
    ):
        if multiline:
            if line.endswith("--"):
                multiline = False
            continue
        elif len(line) >= 4 and line.startswith("--") and line.endswith("--"):
            continue
        elif line.startswith("--"):
            last_comment = lpos
            multiline = True
            continue
        line = line.replace("!::__line__", str(lpos))
        if line.startswith("&"):
            ins, *args = group(line[1:].lstrip())
            args = nest_args(exprs_preruntime(args))
            args = process_args(nframe, args)
            argc = len(args)
            if ins == "set_name" and argc == 1:
                name = str(args[0])
            elif ins == "define_error" and argc == 1:
                error.register_error(args[0])
            elif ins == "extend" and argc == 1:
                if args[0].startswith("{") and args[0].endswith("}"):
                    file = os.path.abspath(get_path_with_lib(args[0][1:-1]))
                else:
                    if name != "__main__":
                        file = os.path.join(os.path.dirname(name), args[0])
                if not os.path.isfile(file):
                    print("File not found:", file)
                    break
                with open(file, "r") as f:
                    res.extend(process_code(f.read(), name=name))
                file = os.path.realpath(file)
                meta_attributes["dependencies"]["dpl"].add(file)
            elif ins == "include" and argc == 1:
                if args[0].startswith("{") and args[0].endswith("}"):
                    file = os.path.abspath(get_path_with_lib(ofile := args[0][1:-1]))
                    search_path = "_std"
                else:
                    file = os.path.join(os.path.dirname(name), (ofile := args[0]))
                    if name != "__main__":
                        file = os.path.join(os.path.dirname(name), file)
                    search_path = "_loc"
                if not os.path.exists(file):
                    error.error(lpos, file, f"Not found while including: {file}")
                    return error.PREPROCESSING_ERROR
                if (me:=mod_s.dpl_import(nframe, file, search_path, loc=os.path.dirname(name))) is None:
                    print(f"python: Something wrong happened...\nLine {lpos}\nFile {name}")
                    return error.PREPROCESSING_ERROR
                (variables, program_code) = me
                nframe[0].update(variables)
                res.extend(program_code)
            elif ins == "use" and argc == 1:
                if args[0].startswith("{") and args[0].endswith("}"):
                    file = os.path.abspath(get_path_with_lib(ofile := args[0][1:-1]))
                    search_path = "_std"
                else:
                    file = os.path.join(os.path.dirname(name), (ofile := args[0]))
                    if name != "__main__":
                        file = os.path.join(os.path.dirname(name), file)
                    search_path = "_loc"
                if not os.path.exists(file):
                    error.error(lpos, file, f"Not found while including: {file}")
                    return error.PREPROCESSING_ERROR
                if mod_s.py_import(nframe, file, search_path, loc=os.path.dirname(name)):
                    print(f"python: Something wrong happened...\nLine {lpos}\nFile {name}")
                    return error.PREPROCESSING_ERROR
            elif ins == "use" and argc == 3 and args[1] == "as":
                if args[0].startswith("{") and args[0].endswith("}"):
                    file = os.path.abspath(get_path_with_lib(ofile := args[0][1:-1]))
                    search_path = "_std"
                else:
                    file = os.path.join(os.path.dirname(name), (ofile := args[0]))
                    if name != "__main__":
                        file = os.path.join(os.path.dirname(name), file)
                    search_path = "_loc"
                if not os.path.exists(file):
                    error.error(lpos, file, f"Not found while including: {file}")
                    return error.PREPROCESSING_ERROR
                if mod_s.py_import(nframe, file, search_path, loc=os.path.dirname(name), alias=args[2]):
                    print(f"python: Something wrong happened...\nLine {lpos}\nFile {name}")
                    return error.PREPROCESSING_ERROR
            elif ins == "import" and argc == 1:
                vname = args[0].rsplit(".", 1)[-1]
                try:
                    nframe[-1][vname] = dict(__import__(args[0]).__dict__)
                except ModuleNotFoundError:
                    error.pre_error(lpos, file, f"Module {args[0]!r} not found.")
                    return error.PREPROCESSING_ERROR
                except:
                    error.pre_error(lpos, file, f"{traceback.format_exc()}\nSomething went wrong while importing {args[0]!r}.")
                    return error.PREPROCESSING_ERROR
            elif ins == "use:luaj" and argc == 1:
                if args[0].startswith("{") and args[0].endswith("}"):
                    file = os.path.abspath(get_path_with_lib(ofile := args[0][1:-1]))
                    search_path = "_std"
                else:
                    if name != "__main__":
                        file = os.path.join(os.path.dirname(name), args[0])
                    search_path = "_loc"
                if mod_s.luaj_import(nframe, file, search_path, loc="."):
                    print(f"use:luaj: Something wrong happened...\nLine {lpos}\nFile {name}")
                    return error.PREPROCESSING_ERROR
            elif ins == "use:c" and argc == 1:
                if args[0].startswith("{") and args[0].endswith("}"):
                    file = os.path.abspath(get_path_with_lib(ofile := args[0][1:-1]))
                    search_path = "_std"
                else:
                    if name != "__main__":
                        file = os.path.join(os.path.dirname(name), args[0])
                    else:
                        file = args[0]
                    search_path = "_loc"
                if errcode:=mod_s.c_import(nframe, file, search_path, loc="."):
                    print(f"use:c: Something wrong happened...\nLine {lpos}\nFile {name}")
                    if errcode == 2:
                        return error.LIBRARY_NOT_FOUND
                    else:
                        return error.PREPROCESSING_ERROR
            elif ins == "use:c" and argc == 3 and args[1] == "as":
                if args[0].startswith("{") and args[0].endswith("}"):
                    file = os.path.abspath(get_path_with_lib(ofile := args[0][1:-1]))
                    search_path = "_std"
                else:
                    if name != "__main__":
                        file = os.path.join(os.path.dirname(name), args[0])
                    search_path = "_loc"
                if mod_s.c_import(nframe, file, search_path, loc=".", alias=args[2]):
                    print(f"use:c: Something wrong happened...\nLine {lpos}\nFile {name}")
                    return error.PREPROCESSING_ERROR
            elif ins == "embed" and argc == 3 and args[1] == "as":
                if args[0] == name:
                    nframe[-1][args[2]] = fcode
                    continue
                file = os.path.join(os.path.dirname(name), args[0])
                if os.path.isfile(file):
                    with open(file) as f:
                        nframe[-1][args[2]] = f.read()
                else:
                    print("File not found:", file)
                    return error.PREPROCESSING_ERROR
            elif ins == "embed_binary" and argc == 3 and args[1] == "as":
                if args[0] == name:
                    nframe[-1][args[2]] = bytes(fcode)
                    continue
                file = os.path.join(os.path.dirname(name), args[0])
                if os.path.isfile(file):
                    with open(file, "rb") as f:
                        nframe[-1][args[2]] = f.read()
                else:
                    print("File not found:", file)
                    return error.PREPROCESSING_ERROR
            elif ins.startswith("enable:") and ins[7:] in preprocessing_flags:
                preprocessing_flags[ins[7:]] = True
            elif ins.startswith("disable:") and ins[8:] in preprocessing_flags:
                preprocessing_flags[ins[8:]] = False
            elif ins == "set" and argc == 2:
                rset(nframe[-1], args[0], args[1])
            else:
                error.error(
                    lpos, name, f"{name!r}:{lpos}: Invalid directive {ins!r}"
                )
                break
        else:
            try:
                l = group(line)
                ins, *args = nest_args(exprs_preruntime(l))
                if isinstance(ins, Expression):
                    try:
                        ins = to_static(ins, env=nframe)
                    except Exception as e:
                        error.error(lpos, file, repr(e))
                        return error.TYPE_ERROR
            except error.DPLError as e:
                error.error(lpos, name, f"Caught error: {error.error_stack[-1]['message']}")
                return e.code
            except Exception as e:
                error.error(lpos, name, traceback.format_exc())
                return error.PREPROCESSING_ERROR
            res.append((lpos, name, ins, None, args))
    else:
        if multiline:
            error.error(
                last_comment,
                name,
                f"{name!r}:{last_comment}: Unclosed multiline comment!",
            )
            return error.PREPROCESSING_ERROR
        # pass for switches pre runtime transformations
        nres = res
        pos = 0
        res = []
        inlines = {}
        while pos < len(nres):
            entire_line = line_pos, file, ins, _, args = nres[pos]
            argc = len(args)
            if not isinstance(ins, str | ID):
                res.append(entire_line)
            elif ins == "switch::static":
                body = {None: []}
                arg_val = args[0]
                og_lpos = line_pos
                temp = get_block(nres, pos)
                if temp is None:
                    error.error(line_pos, file, "Switch statement is invalid!")
                    return error.PREPROCESSING_ERROR
                pos, switch_block = temp
                sub_pos = 0
                while sub_pos < len(switch_block):
                    line_pos, file, ins, _, args = switch_block[sub_pos]
                    if ins == "case" and len(args) == 1:
                        if not is_static([args[0]]):
                            error.error(line_pos, file, f"Case {args[0]!s} is not constant for static::switch at {og_lpos}.")
                            return error.PREPROCESSING_ERROR
                        temp = get_block(switch_block, sub_pos)
                        if temp is None:
                            error.error(line_pos, file, f"Switch statement is invalid! For case '{args[0]}'")
                            return error.PREPROCESSING_ERROR
                        sub_pos, bod = temp
                        body_tag = process_arg(nframe, args[0])
                        if not isinstance(body_tag, str | int | float | set | tuple | ID):
                            body_tag = f"{type(body_tag)}:{repr(body_tag)}"
                        body[body_tag] = process_blocks(None, bod)
                    elif ins == "default" and not args:
                        temp = get_block(switch_block, sub_pos)
                        if temp is None:
                            error.error(line_pos, file, f"Switch statement is invalid! For case '{args[0]}'")
                            return error.PREPROCESSING_ERROR
                        sub_pos, bod = temp
                        body[None] = process_blocks(None, bod)
                    else:
                        error.error(line_pos, file, f"Switch statement is invalid!")
                        return error.SYNTAX_ERROR
                    sub_pos += 1
                res.append([og_lpos, file, "_intern.switch::static", None, [body, arg_val]])
            elif ins == "switch" and argc == 1:
                body = {"default": [], "opts": []}
                opts = body["opts"]
                arg_val = args[0]
                og_lpos = line_pos
                temp = get_block(nres, pos)
                if temp is None:
                    error.error(line_pos, file, "Switch statement is invalid!")
                    return error.PREPROCESSING_ERROR
                pos, switch_block = temp
                sub_pos = 0
                while sub_pos < len(switch_block):
                    line_pos, file, ins, _, args = switch_block[sub_pos]
                    if ins == "case" and len(args) == 1:
                        temp = get_block(switch_block, sub_pos)
                        if temp is None:
                            error.error(line_pos, file, f"Switch statement is invalid! For case '{args[0]}'")
                            return error.PREPROCESSING_ERROR
                        sub_pos, tbody = temp
                        opts.append({
                            "value": args[0],
                            "body": process_blocks(nframe, tbody)
                        })
                    elif ins == "default" and not args:
                        temp = get_block(switch_block, sub_pos)
                        if temp is None:
                            error.error(line_pos, file, f"Switch statement is invalid! For case '{args[0]}'")
                            return error.PREPROCESSING_ERROR
                        sub_pos, bod = temp
                        body["default"] = process_blocks(nframe, bod)
                    else:
                        error.error(line_pos, file, "Invalid switch statement!")
                        return error.PREPROCESSING_ERROR
                    sub_pos += 1
                res.append([og_lpos, file, "_intern.switch::dynamic", None, [body, arg_val]])
            else:
                res.append(entire_line)
            pos += 1
        frame = {
            "code": process_blocks(nframe, res),      # HLIR or LLIR code
            "frame": nframe,  # Stack frame, populated via modules
                              # Is the code HLIR or LLIR?
                              # This will be used in the future
                              # to automatically switch execution functions.
        }
        return frame
    return error.PREPROCESSING_ERROR

@register_run_fn
@argproc_setter.set_run_fn
def run_func(frame, function_obj, *args, line_position="???", module_filepath="???"):
    args = process_args(frame, args)
    nscope(frame)
    if function_obj["self"] is not None:
        frame[-1]["self"] = function_obj["self"]
    frame[-1]["_args"] = args
    if function_obj["variadic"]["name"] != constants.nil:
        if len(args)-1 >= function_obj["variadic"]["index"]:
            variadic = []
            for line_position, [name, value] in enumerate(itertools.zip_longest(function_obj["args"], args)):
                if name in function_obj["checks"]:
                    if not run_func(frame, function_obj["checks"][name], value):
                        error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][4][0]}")
                        raise error.DPLError(error.CHECK_ERROR)
                if variadic:
                    variadic.append(value)
                elif line_position >= function_obj["variadic"]["index"]:
                    variadic.append(value)
                else:
                    frame[-1][name] = value
            frame[-1][function_obj["variadic"]["name"]] = variadic
        else:
            error.error(line_position, module_filepath, f"Function {function_obj['name']} is a variadic and requires {function_obj['variadic']['index']+1} arguments or more.")
            raise error.DPLError(error.CHECK_ERROR)
    else:
        if len(args) != len(function_obj["args"]) and not function_obj["defaults"]:
            text = "more" if len(args) > len(function_obj["args"]) else "less"
            error.error(line_position, module_filepath, f"Function got {text} than expected arguments!\nExpected {len(function_obj['args'])} arguments but got {len(args)} arguments.")
            raise error.DPLError(error.CHECK_ERROR)
        for n, v in function_obj["defaults"].items():
            frame[-1][n] = v
        for name, value in itertools.zip_longest(function_obj["args"], args, fillvalue=constants.nil):
            if name == constants.nil:
                break
            if name in function_obj["checks"]:
                if not run_func(frame, function_obj["checks"][name], value):
                    error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][4][0]}")
                    raise error.DPLError(error.CHECK_ERROR)
            frame[-1][name] = value
    if function_obj["capture"] != constants.nil:
        frame[-1]["_capture"] = function_obj["capture"]
    frame[-1]["_returns"] = ("_internal::return",)
    err = execute(function_obj["body"], frame)
    if err and err != error.STOP_FUNCTION:
        if err > 0:
            error.error(line_position, module_filepath,
            f"Error in function {function_obj['name']!r}: [{err}] {error.ERRORS_DICT.get(err, '???')}")
            raise error.DPLError(err)
    pscope(frame)
    if "_internal::return" in frame[-1]:
        ret = frame[-1]["_internal::return"]
        return ret if isinstance(ret, (list, tuple)) and len(ret) == 1 else ret
    return constants.nil

@mod_s.register_execute
@argproc_setter.set_execute
@varproc.register_execute
def execute(code, frame):
    """
    Low level function to run.
    Unlike the old run function
    on setup it requires less conditions
    per level of recursion.
    Run HLIR,
    Not LLIR.
    This is used internally.
    Use run_code instead for more logic.
    """
    # the contents of the new run_code function
    # was previously here
    # and ran every recursive call

    lrset = rset; lrget = rget
    for line_position, module_filepath, ins, block, oargs in code:
        if isinstance(ins, Expression):
            ins = process_arg(frame, ins)
        try:
            args = process_args(frame, oargs)
            argc = len(args)
        except Exception as e:
            error.error(
                line_position,
                module_filepath,
                f"{traceback.format_exc()}\nSomething went wrong when arguments were processed:\n{e}\n> {oargs!r}",
            )
            return error.PYTHON_ERROR
        ## THREE ARGS
        if argc == 3:
            if ins == "dec":
                lrset(frame[-1], args[0], res if (res:=lrget(frame[-1], args[0], default=0) - 1) > args[1] else args[2])
                continue
            elif ins == "for" and args[1] == "in":
                if block:
                    name, _, iter_ = args
                    if isinstance(name, tuple):
                        index, name = name
                        for ind, i in enumerate(iter_):
                            frame[-1][name] = i
                            frame[-1][index] = ind
                            err = execute(block, frame)
                            if err:
                                if err == STOP_RESULT:
                                    break
                                elif err == SKIP_RESULT:
                                    continue
                                return err
                    else:
                        for i in iter_:
                            frame[-1][name] = i
                            err = execute(block, frame)
                            if err:
                                if err == STOP_RESULT:
                                    break
                                elif err == SKIP_RESULT:
                                    continue
                                return err
                continue
            elif ins == "rfor" and args[1] == "in":
                if block:
                    name, _, iter_ = args
                    if isinstance(name, tuple):
                        index, name = name
                        for ind, i in enumerate(iter_):
                            frame[-1][name] = i
                            frame[-1][index] = ind
                            err = execute(block, frame)
                    else:
                        for i in iter_:
                            frame[-1][name] = i
                            err = execute(block, frame)
                continue
            elif ins == "exec":
                if err:=run(process_code(args[0], name=args[1]), frame=args[2]):
                    return err
                continue
            elif ins == "set" and args[1] == "=":
                if isinstance(args[0], (list, tuple)):
                    for name, value in flatten_dict(unpack(args[0], args[1])).items():
                        print(name, value)
                else:
                    lrset(frame[-1], args[0], args[2])
                continue
            elif ins == "lset" and args[1] == "=":
                frame[-1][args[0]] = args[2]
                continue
            elif ins == "mset" and args[1] == "=":
                if args[0] != "_":
                    if isinstance(args[0], (tuple, list)):
                        for name, value in zip(args[0], args[2]):
                            lrset(frame[-1], name, value, meta=True)
                    else:
                        lrset(frame[-1], args[0], args[2], meta=True)
                continue
            elif ins == "catch":  # catch return value of a function
                rets, func_name, args = args
                if (function_obj := lrget(frame[-1], func_name, default=lrget(frame[0], func_name))) == constants.nil or not isinstance(function_obj, dict):
                    error.error(line_position, module_filepath, f"Invalid function {func_name!r}!")
                    break
                if function_obj["tags"]["preserve-args"]:
                    raw_args = args[0]
                args = process_args(frame, args)
                nscope(frame)
                if function_obj["self"] is not None:
                    frame[-1]["self"] = function_obj["self"]
                if function_obj["tags"]["preserve-args"]:
                    frame[-1]["_raw_args"] = raw_args
                frame[-1]["_args"] = args
                if function_obj["capture"] != constants.nil:
                    frame[-1]["_capture"] = function_obj["capture"]
                if function_obj["variadic"]["name"] != constants.nil:
                    if len(args)-1 >= function_obj["variadic"]["index"]:
                        variadic = []
                        for line_position, [name, value] in enumerate(itertools.zip_longest(function_obj["args"], args)):
                            if name in function_obj["checks"]:
                                if not run_func(frame, func_obj["checks"], value):
                                    error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][4][0]}")
                                    return error.CHECK_ERROR
                            if variadic:
                                variadic.append(value)
                            elif line_position >= function_obj["variadic"]["index"]:
                                variadic.append(value)
                            else:
                                frame[-1][name] = value
                        frame[-1][function_obj["variadic"]["name"]] = variadic
                    else:
                        error.error(line_position, module_filepath, f"Function {ins} is a variadic and requires {function_obj['variadic']['index']+1} arguments or more.")
                        return error.RUNTIME_ERROR
                else:
                    if len(args) != len(function_obj["args"]) and not function_obj["defaults"]:
                        text = "more" if len(args) > len(function_obj["args"]) else "less"
                        error.error(line_position, module_filepath, f"Function got {text} than expected arguments!\nExpected {len(function_obj['args'])} arguments but got {len(args)} arguments.")
                        return error.RUNTIME_ERROR
                    for n, v in function_obj["defaults"].items():
                        frame[-1][n] = v
                    for name, value in itertools.zip_longest(function_obj["args"], args):
                        if name is None:
                            break
                        if name in function_obj["checks"]:
                            if not run_func(frame, function_obj["checks"][name], value):
                                error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][4][0]}")
                                return error.CHECK_ERROR
                        frame[-1][name] = value
                frame[-1]["_returns"] = rets
                err = execute(function_obj["body"], frame)
                if err > 0:
                    error.error(line_position, module_filepath, f"Error in function {ins!r}")
                    return err
                pscope(frame)
                continue
            elif ins == "ecatch":  # catch return value of a python function
                rets, name, args = args
                args = process_args(frame, args)
                if (function := lrget(frame[-1], name, default=lrget(frame[0], name))) == constants.nil or not hasattr(function, "__call__"):
                    error.error(line_position, module_filepath, f"Invalid function {name!r}!")
                    return error.NAME_ERROR
                try:
                    res = function(frame, meta_attributes["internal"]["main_path"], *args)
                    if (
                        res is None
                        and WARNINGS
                        and is_debug_enabled("warn_no_return")
                    ):
                        error.warn(
                            "Function doesnt return anything. To reduce overhead please dont use pycatch.\nLine {line_position}\nFile {module_filepath}"
                        )
                    if isinstance(res, tuple):
                        if rets != "_":
                            for name, value in zip(rets, res):
                                lrset(frame[-1], name, value)
                    elif isinstance(res, int) and res:
                        return res
                    elif isinstance(res, str):
                        if res == "err":
                            break
                        elif res == "stop":
                            return error.STOP_RESULT
                        elif res == "skip":
                            return error.SKIP_RESULT
                        elif res.startswith("err:"):
                            _, ecode, message = res.split(":", 2)
                            error.error(line_position, module_filepath, message)
                            return int(ecode)
                except:
                    error.error(line_position, module_filepath, traceback.format_exc()[:-1])
                    return error.PYTHON_ERROR
                continue
        ## NO ARGS
        if ins == "pass": continue
        if ins == "doc": continue
        if argc == 0:
            if ins == "ifmain":
                if module_filepath == "__main__":
                    err = execute(block, frame=frame)
                    if err:
                        return err
                continue
            elif ins == "loop":
                if block:
                    while True:
                        err = execute(block, frame)
                        if err:
                            if err == error.STOP_RESULT:
                                break
                            elif err == error.SKIP_RESULT:
                                continue
                            return err
                continue
            elif ins == "dump_scope":
                pprint(frame[-1])
                continue
            elif ins == "stop":
                return STOP_RESULT
            elif ins == "skip":
                return SKIP_RESULT
            elif ins == "fallthrough":
                return error.FALLTHROUGH
            elif ins == "on_new_scope":
                body = block

                def make_on_new_scope_fn(ons_b, parent_frame):
                    def on_new_scope_tmp_fn(scope, scope_id):
                        fr = new_frame()
                        fr[0]["scope"] = scope
                        fr[0]["scope_id"] = scope_id
                        fr[0]["globals"] = parent_frame[0]
                        return execute(ons_b, fr)
                    return on_new_scope_tmp_fn
                on_new_scope.append({
                    "func": make_on_new_scope_fn(body, frame),
                    "from": f"dpl:{module_filepath}:{line_position}"
                })
                continue
            elif ins == "on_pop_scope":
                body = block

                def make_on_new_scope_fn(ons_b, parent_frame):
                    def on_new_scope_tmp_fn(scope, scope_id):
                        fr = new_frame()
                        fr[0]["scope"] = scope
                        fr[0]["scope_id"] = scope_id
                        fr[0]["globals"] = parent_frame[0]
                        return execute_async(ons_b, fr)
                    return on_new_scope_tmp_fn
                on_pop_scope.append({
                    "func": make_on_new_scope_fn(body, frame),
                    "from": f"dpl:{module_filepath}:{line_position}"
                })
                continue
            elif ins == "START_TIME":
                start_time = time.perf_counter()
                continue
            elif ins == "STOP_TIME":
                end_time = time.perf_counter() - start_time
                continue
            elif ins == "LOG_TIME":
                ct, unit = utils.convert_sec(time.perf_counter() - start_time)
                error.info(f"Elapsed time: {ct:,.8f}{unit}")
                continue
            elif ins == "exit":
                sys.exit()
            elif ins == "repl":
                investigation_repl(frame)
                continue
        ## ONE ARG
        if argc == 1:
            if ins == "inc":
                lrset(frame[-1], args[0], lrget(frame[-1], args[0], default=0) + 1)
                continue
            elif ins == "loop":
                if block:
                    for _ in itertools.repeat(None,args[0]):
                        err = execute(block, frame)
                        if err:
                            if err == error.STOP_RESULT:
                                break
                            elif err == error.SKIP_RESULT:
                                continue
                            return err
                continue
            elif ins == "dec":
                lrset(frame[-1], args[0], lrget(frame[-1], args[0], default=0) - 1)
                continue
            elif ins == "use":
                if args[0].startswith("{") and args[0].endswith("}"):
                    f = os.path.abspath(get_path_with_lib(ofile := args[0][1:-1]))
                    search_path = "_std"
                else:
                    f = os.path.join(os.path.dirname(name), (ofile := args[0]))
                    if name != "__main__":
                        f = os.path.join(os.path.dirname(name), f)
                    search_path = "_loc"
                if not os.path.exists(f):
                    error.error(lpos, module_filepath, f"Not found while including: {f}")
                    return error.PREPROCESSING_ERROR
                if mod_s.py_import(frame, f, search_path, loc=os.path.dirname(module_filepath)):
                    print(f"python: Something wrong happened...\nLine {line_position}\nFile {module_filepath}")
                    return error.RUNTIME_ERROR
                continue
            elif ins == "if":
                if args[0]:
                    err = execute(block, frame=frame)
                    if err:
                        return err
                continue
            elif ins == "sleep" and isinstance(args[0], (int, float)):
                time.sleep(args[0])
                continue
            elif ins == "match":
                if (err := parse_match(frame, block, args[0])) > 0:
                    return err
                continue
            elif ins == "get_time":
                lrset(frame[-1], args[0], time.time())
                continue
            elif ins == "dump_vars" and isinstance(args[0], dict):
                pprint(args[0], hide=False)
                continue
            elif ins == "dump_vars_fancy":
                d = {args[0]: lrget(frame[-1], args[0], meta=True)}
                pprint(d, hide=False)
                continue
            elif ins == "while":
                expr = Expression(args[0])
                if block:
                    while evaluate(frame, expr):
                        err = execute(block, frame)
                        if err:
                            if err == error.STOP_RESULT:
                                break
                            elif err == error.SKIP_RESULT:
                                continue
                            return err
                continue
            elif ins == "enum":
                name = args[0]
                names = set()
                for _, _, ins, _ in block:
                    names.add(ins)
                tmp = frame[-1][name] = {}
                for n in names:
                    tmp[n] = f"enum:{module_filepath}:{name}:{n}"
                continue
            elif ins == "object":
                lrset(frame[-1], args[0], make_object(args[0], frame))
                continue
            elif ins == "make_cons":
                attrs = list(name for name, value in args[0].items() if not name.startswith("_") and not isinstance(value, function_type))
                func = make_method("new", [
                    (line_position, f"{module_filepath}:internal", "new", [":self", "tmp"]),
                    *[
                        (line_position, f"{module_filepath}:internal", "set", [f"tmp.{name}", "=", f":{name}"])
                        for name in attrs
                    ],
                    (line_position, f"{module_filepath}:internal", "return", [":tmp"]),
                ] , attrs, args[0])
                args[0]["new"] = func
                continue
            elif ins == "help":
                if isinstance(args[0], str):
                    args[0] = lrget(frame[-1], args[0])
                if isinstance(args[0], dict):
                    print(f"{args[0].__repr__(less=True)}:\n  {args[0].get('help', 'no docs').replace(chr(10), chr(10)+'  ')}")
                else:
                    print(f"{getattr(args[0], '__name__', '???')}{inspect.signature(args[0])}:\n  {getattr(args[0], '__doc__', 'no docs').replace(chr(10), chr(10)+'  ')}")
                continue
            elif ins == "dict":
                if parse_dict(frame, args[0], block):
                    break
                continue
            elif ins == "list":
                if parse_list(frame, args[0], block):
                    break
                continue
            elif ins == "tuple":
                if parse_tuple(frame, args[0], block):
                    break
                continue
            elif ins == "LOG_TIME":
                ct, unit = utils.convert_sec(time.perf_counter() - start_time)
                error.info(f"Elapsed time: {ct:,.8f}{unit} {args[0]}")
                continue
            elif ins == "local":
                execute(args[0]["body"], frame)
            elif ins == "cmd" :
                os.system(args[0])
                continue
            elif ins == "exit":
                sys.exit(args[0])
            elif ins == "raise" and isinstance(args[0], int):
                error.error(line_position, module_filepath, f"Error [{args[0]}]: {error.ERRORS_DICT.get(args[0], '???')}")
                return args[0]
            elif ins == "assert":
                if not args[0]:
                    error.error(line_position, module_filepath, f"Error [ASSERTION_ERROR]: Assertion failed for {oargs[0]}!")
                    return error.ASSERTION_ERROR
                continue
            elif ins == "happy_assert":
                if not args[0]:
                    error.info_assert_false(line_position, module_filepath, oargs[0])
                    return error.ASSERTION_ERROR
                error.info_assert_true(line_position, module_filepath, oargs[0])
                continue
            elif ins == "string":
                if parse_string(frame, args[0], block, False):
                    break
                continue
        ## VARIADIC >= 1
        if ins == "del" and argc >= 1:
            for name in args:
                rpop(frame[-1], name)
            continue
        ## TWO ARGS
        if argc == 2:
            if ins == "inc":
                lrset(frame[-1], args[0], res if (res:=lrget(frame[-1], args[0], default=0) + 1) < args[1] else 0)
                continue
            elif ins == "check":
                name, body = args
                fn = make_function(frame[-1], name, [(0, "::internal", "return", [], [Expression(body)])], ("self",))
                lrset(frame[-1], name, fn)
                continue
            elif ins == "_intern.switch::static" :
                body_tag = args[1]
                if not isinstance(body_tag, str | int | float | set | tuple | ID):
                    body_tag = f"{type(body_tag)}:{repr(body_tag)}"
                temp_body = args[0].get(body_tag, args[0][None])
                if not temp_body:
                    continue
                if err:= execute(temp_body, frame):
                    error.error(line_position, module_filepath, f"Error in switch block '{args[1]}'")
                    return err
                continue
            elif ins == "_intern.switch::dynamic":
                blocks, arg = args
                for block in blocks["opts"]:
                    if process_arg(frame, block["value"]) == arg:
                        if (err:=execute(block["body"], frame)):
                            if err > 0:
                                error.error(line_position, module_filepath, f"Error in switch case {block['value']!r}: [{err}] {error.ERRORS_DICT.get(err, '???')}")
                            return err
                        if err != error.FALLTHROUGH:
                            break
                else:
                    if (err:=execute(blocks["default"], frame)):
                        if err > 0:
                            error.error(line_position, module_filepath, f"Error in switch case default: [{err}] {error.ERRORS_DICT.get(err, '???')}")
                        return err
                continue
            elif ins == "_intern.match::pattern":
                blocks, arg = args
                for block in blocks["opts"]:
                    if (res:=match_pattern(block["value"], arg)) is not None:
                        for v, t in zip(res.values(), block["types"]):
                            if not isinstance(v, t):
                                break
                        else:
                            frame[-1].update(res)
                            if (err:=execute(block["body"], frame)):
                                if err > 0:
                                    error.error(line_position, module_filepath, f"Error in match::pattern case {block['value']!r}: [{err}] {error.ERRORS_DICT.get(err, '???')}")
                                return err
                            if err != error.FALLTHROUGH:
                                break
                else:
                    if (err:=execute(blocks["default"], frame)):
                        if err > 0:
                            error.error(line_position, module_filepath, f"Error in match::pattern case default: [{err}] {error.ERRORS_DICT.get(err, '???')}")
                        return err
                continue
            elif ins == "new":
                object_scope, object_name = args
                if object_scope == constants.nil:
                    error.error(line_position, module_filepath, f"Unknown object")
                    break
                obj = copy(object_scope)
                for name, value in obj.items():
                    if isinstance(value, function_type):
                        value["self"] = obj
                lrset(frame[-1], object_name, obj)
                continue
            elif ins == "string" and args[1] == "new_line":
                if parse_string(frame, args[0], block, True):
                    break
                continue
            elif ins == "raise" and isinstance(args[0], int):
                error.error(line_position, module_filepath, args[1])
                return args[0]
            elif ins == "cmd":
                frame[-1][args[1]] = os.system(args[0])
                continue
            elif ins == "assert":
                if not args[0]:
                    error.error(line_position, module_filepath, f"Error [ASSERTION_ERROR]: {args[1]}")
                    return error.ASSERTION_ERROR
                continue
        ## VARIADIC >= 2
        if argc >= 2:
            if ins == "fn":
                function_name, params, *tags = args
                func = make_function(frame[-1], function_name, block, process_args(frame, params))
                doc = []
                for _, _, ins, _, args in block:
                    if ins == "doc" and len(args) == 1:
                        doc.append(process_arg(frame, args[0]))
                if doc:
                    func["help"] = "\n".join(doc)
                func["capture"] = frame[-1]
                entry_point = False
                if function_name.endswith("::entry_point"):
                    entry_point = True
                for tag in tags:
                    if tag == "entry_point":
                        entry_point = True
                    if isinstance(tag, (str, ID)):
                        func["tags"][tag] = True
                    elif isinstance(tag, dict):
                        (tag, value), = tag.items()
                        func["tags"][tag] = value
                    elif isinstance(tag, tuple) and len(tag) == 2 and tag[0] in tag_handlers:
                        if (err:=tag_handlers[tag[0]](frame, module_filepath, func, *process_args(frame, tag[1]))):
                            if err > 0: # ignore control codes
                                error.error(line_position, module_filepath, f"Tag handler {tag[0]} raised an error!")
                            return err
                    else:
                        error.error(line_position, module_filepath, f"Invalid tag: {tag!r}")
                        return error.RUNTIME_ERROR
                frame[-1][function_name] = func

                if entry_point and module_filepath == "__main__":
                    function_obj = func
                    raw_args = args = (meta_attributes["argc"], meta_attributes["argv"])
                    nscope(frame).update({
                        "_returns": ("_return_code",)
                    })
                    if function_obj["tags"]["preserve-args"]:
                        frame[-1]["_raw_args"] = raw_args
                    frame[-1]["_args"] = args
                    for n, v in function_obj["defaults"].items():
                        frame[-1][n] = v
                    for name, value in itertools.zip_longest(function_obj["args"], args, fillvalue=constants.nil):
                        if name == constants.nil:
                            break
                        frame[-1][name] = value
                    if function_obj["capture"] != constants.nil:
                        frame[-1]["_capture"] = function_obj["capture"]
                    err = execute(function_obj["body"], frame)
                    if err and err != error.STOP_FUNCTION:
                        if err > 0: error.error(line_position, module_filepath, f"Error in function {function_name!r}: [{err}] {error.ERRORS_DICT.get(err, '???')}")
                        return err
                    if "_return_code" in frame[-1]["_nonlocal"]:
                        ecode = frame[-1]["_nonlocal"]["_return_code"]
                        if ecode > 0:
                            if not isinstance(frame[-1]["_nonlocal"]["_return_code"], int):
                                error.error(line_position, module_filepath, "entry point returned non int return code.")
                                return error.TYPE_ERROR
                            error.error(line_position, module_filepath, f"Entry point function returned error code {ecode}: {error.ERRORS_DICT.get(ecode, '???')}")
                        return ecode
                    pscope(frame)
                    return 0
                continue
            elif ins == "method":
                name, params = args
                scope_name, method_name = name.as_class_method
                self = lrget(frame[-1], scope_name)
                if self == constants.nil:
                    error.error(
                        line_position, module_filepath, "Cannot bind a method to a value that isnt a scope!"
                    )
                    return error.RUNTIME_ERROR
                func = make_method(frame[-1], method_name, block, process_args(frame, params), self)
                self[method_name] = func
                doc = []
                for _, _, ins, _, args in block:
                    if ins == "doc" and len(args) == 1:
                        doc.append(process_arg(frame, args[0]))
                if doc:
                    func["help"] = "\n".join(doc)
                continue
        ## FOUR ARGS
        if argc == 4:
            if ins == "sexec":
                error.silent()
                frame[-1][args[0]] = execute(process_code(args[1], name=args[2]), frame=args[3])
                error.active()
                continue
            elif ins == "string" and args[1] == "new_line" and args[2] == "as":
                if parse_string(frame, args[0], block, True, args[3]):
                    break
                continue
        ## FIVE ARGS
        if argc == 5:
            if ins == "set" and args[1] == "=" and args[3] == "satisfies":
                name, _, value, _, predicates = args
                fn_pred = []
                for i in predicates:
                    if (f:=lrget(frame[-1], i)) == constants.nil:
                        error.error(line_position, module_filepath, f"Check {i!r} does not exist!")
                        return error.CHECK_ERROR
                    fn_pred.append(f)
                if isinstance(args[0], (tuple, list)):
                    for n, v in zip(name, value):
                        for fn in fn_pred:
                            if not run_func(frame, fn, v):
                                error.error(line_position, module_filepath, f"Variable {n!r} ({v!r}) did not pass check {fn['name']}({fn['body'][0][4][0]})")
                                return error.CHECK_ERROR
                        lrset(frame[-1], name, value)
                else:
                    for fn in fn_pred:
                        if not run_func(frame, fn, value):
                            error.error(line_position, module_filepath, f"Variable {name!r} ({value!r}) did not pass check {fn['name']}({str(fn['body'][0][4][0])[1:-1]})")
                            return error.CHECK_ERROR
                    lrset(frame[-1], name, value)
                continue
            elif ins == "inherit" and args[1] == "from" and args[3] == "for":
                attrs, _, parent, _, child = args
                if attrs == "all":
                    for attr in parent:
                        if attr.startswith("_"):
                            continue
                        val = copy(lrget(parent, attr))
                        if isinstance(val, function_type):
                            val["self"] = child
                        lrset(child, attr, val)
                else:
                    for attr in attrs:
                        if attr in parent:
                            val = copy(lrget(parent, attr))
                            if isinstance(val, function_type):
                                val["self"] = child
                            lrset(child, attr, val)
                continue
            elif ins == "safe" and args[0] == "catch":  # catch return value of a function
                _, ecode, rets, func_name, args = args
                if (function_obj := lrget(frame[-1], func_name, default=lrget(frame[0], func_name))) == constants.nil or not isinstance(function_obj, dict):
                    error.error(line_position, module_filepath, f"Invalid function {func_name!r}!")
                    break
                if function_obj["tags"]["preserve-args"]:
                    raw_args = args[0]
                args = process_args(frame, args)
                nscope(frame)
                if function_obj["self"] is not None:
                    frame[-1]["self"] = function_obj["self"]
                if function_obj["tags"]["preserve-args"]:
                    frame[-1]["_raw_args"] = raw_args
                frame[-1]["_args"] = args
                if function_obj["capture"] != constants.nil:
                    frame[-1]["_capture"] = function_obj["capture"]
                if function_obj["variadic"]["name"] != constants.nil:
                    if len(args)-1 >= function_obj["variadic"]["index"]:
                        variadic = []
                        for line_position, [name, value] in enumerate(itertools.zip_longest(function_obj["args"], args)):
                            if name in function_obj["checks"]:
                                if not run_func(frame, func_obj["checks"], value):
                                    error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][4][0]}")
                                    return error.RUNTIME_ERROR
                            if variadic:
                                variadic.append(value)
                            elif line_position >= function_obj["variadic"]["index"]:
                                variadic.append(value)
                            else:
                                frame[-1][name] = value
                        frame[-1][function_obj["variadic"]["name"]] = variadic
                    else:
                        error.error(line_position, module_filepath, f"Function {ins} is a variadic and requires {function_obj['variadic']['index']+1} arguments or more.")
                        return error.RUNTIME_ERROR
                else:
                    if len(args) != len(function_obj["args"]) and not function_obj["defaults"]:
                        text = "more" if len(args) > len(function_obj["args"]) else "less"
                        error.error(line_position, module_filepath, f"Function got {text} than expected arguments!\nExpected {len(function_obj['args'])} arguments but got {len(args)} arguments.")
                        return error.RUNTIME_ERROR
                    for n, v in function_obj["defaults"].items():
                        frame[-1][n] = v
                    for name, value in itertools.zip_longest(function_obj["args"], args):
                        if name is None:
                            break
                        if name in function_obj["checks"]:
                            if not run_func(frame, function_obj["checks"][name], value):
                                error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][4][0]}")
                                return error.RUNTIME_ERROR
                        frame[-1][name] = value
                frame[-1]["_returns"] = rets
                error.silent()
                err = execute(function_obj["body"], frame)
                error.active()
                pscope(frame)
                if err > 0:
                    frame[-1][ecode] = err
                continue
        # SIX ARGS
        if argc == 6:
            if ins == "set" and args[1] == "=" and args[3] == "satisfies" and args[4] == "check":
                if args[0] != "_":
                    name, _, value, _, _, predicate = args
                    fn_pred = make_function(frame[-1], f"check::{name}", [ (0, "::internal", "return", [], [ Expression(predicate) ]) ], ("self",))
                    if isinstance(args[0], (tuple, list)):
                        for n, v in zip(name, value):
                            if not run_func(frame, fn_pred, v):
                                error.error(line_position, module_filepath, f"Variable {n!r} ({v!r}) did not pass check {fn_pred['name']}({fn_pred['body'][0][4][0]})")
                                return error.CHECK_ERROR
                            lrset(frame[-1], name, value)
                    else:
                        if not run_func(frame, fn_pred, value):
                            error.error(line_position, module_filepath, f"Variable {name!r} ({value!r}) did not pass check {fn_pred['name']}({str(fn_pred['body'][0][4][0])[1:-1]})")
                            return error.CHECK_ERROR
                        lrset(frame[-1], name, value)
                continue
        # MISC
        if ins == "return":  # Return to the latched names
            if (latched_names := lrget(frame[-1], "_returns")) != constants.nil:
                if latched_names == "_":
                    return error.STOP_FUNCTION
                if len(latched_names) == 1:
                    lrset(
                        frame[-1]["_nonlocal"],
                        latched_names[0],
                        args[0]
                            if isinstance(args, (tuple, list))
                            and len(args) == 1
                        else args)
                else:
                    for name, value in zip(latched_names, args):
                        lrset(frame[-1]["_nonlocal"], name, value)
            return error.STOP_FUNCTION
        if isinstance(ins, (str, ID)) and (
            (function_obj := lrget(frame[-1], ins, default=lrget(frame[0], ins)))
            != constants.nil
            and isinstance(function_obj, dict)
            and "body" in function_obj and
                "args" in function_obj and
                "capture" in function_obj and
                argc == 1
            ):  # Call a function
            args = process_args(frame, args[0])
            nscope(frame)
            if function_obj["self"] is not None:
                frame[-1]["self"] = function_obj["self"]
            frame[-1]["_args"] = args
            if function_obj["variadic"]["name"] != constants.nil:
                if len(args)-1 >= function_obj["variadic"]["index"]:
                    variadic = []
                    for line_position, [name, value] in enumerate(itertools.zip_longest(function_obj["args"], args)):
                        if name in function_obj["checks"]:
                            if not run_func(frame, func_obj["checks"], value):
                                error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][4][0]}")
                                return error.CHECK_ERROR
                        if variadic:
                            variadic.append(value)
                        elif line_position >= function_obj["variadic"]["index"]:
                            variadic.append(value)
                        else:
                            frame[-1][name] = value
                    frame[-1][function_obj["variadic"]["name"]] = variadic
                else:
                    error.error(line_position, module_filepath, f"Function {ins} is a variadic and requires {function_obj['variadic']['index']+1} arguments or more.")
                    return error.RUNTIME_ERROR
            else:
                if len(args) != len(function_obj["args"]) and not function_obj["defaults"]:
                    text = "more" if len(args) > len(function_obj["args"]) else "less"
                    error.error(line_position, module_filepath, f"Function got {text} than expected arguments!\nExpected {len(function_obj['args'])} arguments but got {len(args)} arguments.")
                    return error.RUNTIME_ERROR
                for n, v in function_obj["defaults"].items():
                    frame[-1][n] = v
                for name, value in itertools.zip_longest(function_obj["args"], args, fillvalue=constants.nil):
                    if name == constants.nil:
                        break
                    if name in function_obj["checks"]:
                        if not run_func(frame, function_obj["checks"][name], value):
                            error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][4][0]}")
                            return error.CHECK_ERROR
                    frame[-1][name] = value
            if function_obj["capture"] != constants.nil:
                frame[-1]["_capture"] = function_obj["capture"]
            err = execute(function_obj["body"], frame)
            if err and err != error.STOP_FUNCTION:
                if err > 0: error.error(line_position, module_filepath, f"Error in function {ins!r}: [{err}] {error.ERRORS_DICT.get(err, '???')}")
                return err
            pscope(frame)
            continue
        if (
            (function_obj := ins)
            != constants.nil
            and isinstance(function_obj, dict)
            and "body" in function_obj and
                "args" in function_obj and
                "capture" in function_obj and
                argc == 1
            ):  # Call a function
            if function_obj["tags"]["preserve-args"]:
                raw_args = args[0]
            args = process_args(frame, args[0])
            nscope(frame)
            if function_obj["tags"]["preserve-args"]:
                frame[-1]["_raw_args"] = raw_args
            if function_obj["self"] is not None:
                frame[-1]["self"] = function_obj["self"]
            frame[-1]["_args"] = args
            if function_obj["variadic"]["name"] != constants.nil:
                if len(args)-1 >= function_obj["variadic"]["index"]:
                    variadic = []
                    for line_position, [name, value] in enumerate(itertools.zip_longest(function_obj["args"], args)):
                        if name in function_obj["checks"]:
                            if not run_func(frame, func_obj["checks"], value):
                                error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][4][0]}")
                                return error.CHECK_ERROR
                        if variadic:
                            variadic.append(value)
                        elif line_position >= function_obj["variadic"]["index"]:
                            variadic.append(value)
                        else:
                            frame[-1][name] = value
                    frame[-1][function_obj["variadic"]["name"]] = variadic
                else:
                    error.error(line_position, module_filepath, f"Function {ins} is a variadic and requires {function_obj['variadic']['index']+1} arguments or more.")
                    return error.RUNTIME_ERROR
            else:
                if len(args) != len(function_obj["args"]) and not function_obj["defaults"]:
                    text = "more" if len(args) > len(function_obj["args"]) else "less"
                    error.error(line_position, module_filepath, f"Function got {text} than expected arguments!\nExpected {len(function_obj['args'])} arguments but got {len(args)} arguments.")
                    return error.RUNTIME_ERROR
                for n, v in function_obj["defaults"].items():
                    frame[-1][n] = v
                for name, value in itertools.zip_longest(function_obj["args"], args, fillvalue=constants.nil):
                    if name == constants.nil:
                        break
                    if name in function_obj["checks"]:
                        if not run_func(frame, function_obj["checks"][name], value):
                            error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][4][0]}")
                            return error.CHECK_ERROR
                    frame[-1][name] = value
            if function_obj["capture"] != constants.nil:
                frame[-1]["_capture"] = function_obj["capture"]
            err = execute(function_obj["body"], frame)
            if err and err != error.STOP_FUNCTION:
                if err > 0: error.error(line_position, module_filepath, f"Error in function {ins!r}: [{err}] {error.ERRORS_DICT.get(err, '???')}")
                return err
            pscope(frame)
            continue
        if (
            function := lrget(frame[-1], ins, default=lrget(frame[0], ins))
        ) != constants.nil and hasattr(
            function, "__call__"
        ):  # call a python function

            # Even I dont under stand this now...
            # good luck future me
            args = process_args(frame, args[0])
            try:
                res = function(frame, module_filepath, *args)
                if isinstance(res, int) and res:
                    return res
                elif isinstance(res, str):
                    if res == "break":
                        break
                    elif res.startswith("err:"):
                        _, ecode, message = res.split(":", 2)
                        error.error(line_position, module_filepath, message)
                        return int(ecode)
            except:
                error.error(line_position, module_filepath, traceback.format_exc()[:-1])
                return error.PYTHON_ERROR
            continue
        if not isinstance((obj := lrget(frame[-1], ins)), dict) and obj in (
            None,
            constants.none,
        ):
            print(
                "\nAdditional Info: User may have called a partially defined function!",
                end="",
            )
        error.error(line_position, module_filepath, f"Invalid instruction {ins}")
        return error.RUNTIME_ERROR
    else:
        return 0
    error.error(line_position, module_filepath, "Error was raised!")
    return error.SYNTAX_ERROR


class IsolatedParser:
    def __init__(self, file_name="__main__", main_path=".", libdir=PERM_LIBDIR, argv=None):
        self.defaults = {
            "libdir": PERM_LIBDIR,
            "argv": ARGV.copy(),
            "main_file": varproc.internal_attributes["main_file"],
            "main_path": varproc.internal_attributes["main_path"],
            "meta": copy(varproc.meta_attributes),
        }
        varproc.internal_attributes["main_file"] = file_name
        varproc.internal_attributes["main_path"] = main_path
        LIBDIR = libdir

    def __enter__(self):
        return self

    def run_code(self, code, frame=None):
        if isinstance(code, str):
            code = process_code(code)
        return run_code(code, frame=frame)

    def __exit__(self, exc, exc_ins, tb):
        LIBDIR = self.defaults["libdir"]
        ARGV = self.defaults["argv"]
        varproc.internal_attributes["main_file"] = self.defaults["main_file"]
        varproc.internal_attributes["main_path"] = self.defaults["main_path"]
        varproc.meta_attributes.update(self.defaults["meta"])
        return False


def investigation_repl(frame, err=0):
    print("\nDebugging REPL\n  enter 'exit' to exit program\n  enter 'debug-exit' to exit the REPL\n  enter 'debug-error' to see the error\n  enter 'debug-help' for info")
    if err:
        frame[-1]["_error"] = err
    while True:
        act = input(">>> ").strip()
        if act == "debug-help":
            print('''Debugging REPL 1.0

This REPL is invoked when your program crashes
or when manually invoked using the 'repl' instruction.
This REPL can help you investigate why your
program crashed, instead of running an external
debugger, we have the debugger here instead!''')
            continue
        elif act == "debug-exit":
            break
        elif act == "debug-error":
            if err:
                print(f"Raised Error: {err} - {error.ERRORS_DICT[err]}")
                if error.error_stack:
                    pos, file, message, _ = error.error_stack[-1].values()
                    print(f"Line {pos} in file {file}\nCause: {message}")
            else:
                print(f"No error.")
            continue
        elif act and act.split(maxsplit=1)[0] in INCREMENTS:
            while True:
                act1 = input("... ").strip()
                if not act1:
                    break
                else:
                    act += "\n" + act1
        if e:=run_code(process_code(act), frame) > 0:
            print(f"\nError ({e}: {error.ERRORS_DICT[e]}):\nSome error happened.")

# Versions below 1.4.8 and some 1.4.8
# builds ran the code inside this function
# recursively affecting performance
def run_code(code, frame=None):
    """
    Run code generated by 'process_code'
    The code below only needs to run
    at depth=1 so we dont need to run these
    every scope that needs to run.
    More performance! Yum ;)
    """
    if isinstance(code, int):
        return code
    elif isinstance(code, dict):
        code, nframe = code["code"], code["frame"]
    elif isinstance(code, list):
        err = execute(code, frame)
        if err and varproc.preprocessing_flags["REPL_ON_ERROR"]:
            investigation_repl(frame, err)
        return err
    else:
        nframe = new_frame()
    if frame is not None:
        frame[0].update(nframe[0])
    else:
        frame = nframe
    
    # Run using old parser
    # the function below is recursive
    # thats why depth was mentioned
    # in the doc string.
    try:
        err = execute(code, frame)
        if err and varproc.preprocessing_flags["REPL_ON_ERROR"]:
            investigation_repl(frame, err)
        return err
    except error.DPLError as e:
        return e.code
    except (SystemExit, KeyboardInterrupt) as e:
        raise e
    except:
        print(traceback.format_exc()+"\nPLEASE REPORT THIS BUG FOR IT ISNT EXPECTED!")
        return error.PYTHON_ERROR


def get_run():
    return run_code


##################################
#       for -get-internals       #
##################################
# Do not modify without permission

# this allows the user
# to basically give them the freedom
# to make internal tooling
# in DPL possible
# in the future especially for LLIR
# even define their own DSLs in DPL

if "get-internals" in program_flags:
    varproc.meta_attributes["runtime_processing"] = {
        "process_code": lambda _, __, *args: (process_code(*args),),
        "execute_code": lambda _, __, *args: (execute(*args),),
        "run_code": lambda _, __, *args: (run_code(*args),),
        "get_block": lambda _, __, *args: get_block(*args),
    }

##################################
#      BEWARE DARK SOURCERY      #
##################################
# this is classified as dark magic...

mod_s.dpl.execute = execute
mod_s.dpl.call_dpl = run_func
mod_s.dpl.process_code = process_code

# Some of the functions here have been turned into decorators
