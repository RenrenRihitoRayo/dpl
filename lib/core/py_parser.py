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
from . import info
import multiprocessing
import threading
import traceback
import sys
import os
import gc
import threading
arguments_handler = py_argument_handler.arguments_handler

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

pp2_execute = None
process_hlir = None

output_stack_lock = threading.Lock()
output_stack = []

meta_attributes["output_stack"] = output_stack

def register_execute(func):
    global pp2_execute
    pp2_execute = func

def register_process_hlir(func):
    global process_hlir
    process_hlir = func

def get_block(code, current_p, supress=False, start=1):
    "Get a code block. Runtime! (helps init become faster)"
    instruction_pointer = current_p + 1
    line_position, file, ins, _ = code[instruction_pointer]
    k = start
    if k == 0 and ins not in info.INCREAMENTS:
        error.error(line_position, file, "Expected to have started with an instruction that indents.")
        return None
    res = []
    while instruction_pointer < len(code):
        _, _, ins, _ = code[instruction_pointer]
        if ins in info.INC_EXT:
            k += 1
        elif ins in info.INC:
            k += info.INC[ins]
        elif ins in info.DEC:
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
    if isinstance(d, objects.objects):
        print(("  "*l+repr(d))+",")
        return
    seen.add(id(d))
    if isinstance(d, list):
        for i in d:
            if isinstance(i, list):
                print("  "*l+"[")
                pprint(i, l+1, seen)
                print("  "*l+"],")
            elif isinstance(d, objects.objects):
                print(("  "*l+repr(d))+",")
            elif isinstance(i, objects.object_type):
                print("  "*l+f"{i['_type_name']}{{")
                pprint(i, l+1, seen)
                print("  "*l+"},")
            elif isinstance(i, dict):
                print("  "*l+"{")
                pprint(i, l+1, seen)
                print("  "*l+"},")
            else:
                print("  "*l+repr(i)+",")
        return
    elif not isinstance(d, dict):
        print("  "*l+repr(d)+",")
        return
    if not d:
        print("{},")
        return
    for name, value in d.items():
        if isinstance(name, str) and name.startswith("_") and hide:
            ...
        elif isinstance(value, objects.objects):
            print(("  "*l+f"{name!r}: " + repr(value))+",")
        elif isinstance(value, objects.object_type):
            print("  "*l+f"{name!r}: {value['_type_name']}{{")
            pprint(value, l+1, seen)
            print("  "*l+"},")
        elif isinstance(value, dict):
            print("  "*l+f"{name!r}: {{")
            pprint(value, l+1, seen)
            print("  "*l+"},")
        elif isinstance(value, list):
            print("  "*l+f"{name!r}: [")
            pprint(value, l+1, seen)
            print("  "*l+"],")
        else:
            print("  "*l+f"{name!r}: {value!r},")


def recursive_replace(data, target, replacement):
    if isinstance(data, (str, bytes)):
        return replacement if data == target else data
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
    for [line_pos, module_name, ins, args] in body:
        nargs = args
        for name, value in values:
            current_name = f"::{name}"
            ins, nargs = recursive_replace([ins, nargs], current_name, value)
        res.append((line_pos, module_name, ins, to_static(nargs) if varproc.meta_attributes["preprocessing_flags"]["EXPRESSION_FOLDING"] else nargs))
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
                    file = os.path.abspath(info.get_path_with_lib(args[0][1:-1]))
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
                    file = os.path.abspath(info.get_path_with_lib(ofile := args[0][1:-1]))
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
                    file = os.path.abspath(info.get_path_with_lib(ofile := args[0][1:-1]))
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
                    file = os.path.abspath(info.get_path_with_lib(ofile := args[0][1:-1]))
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
                    file = os.path.abspath(info.get_path_with_lib(ofile := args[0][1:-1]))
                    search_path = "_std"
                else:
                    if name != "__main__":
                        file = os.path.join(os.path.dirname(name), args[0])
                    search_path = "_loc"
                if mod_s.luaj_import(nframe, file, search_path, loc="."):
                    print(f"luaj: Something wrong happened...\nLine {lpos}\nFile {name}")
                    return error.PREPROCESSING_ERROR
            elif ins == "use:c" and argc == 1:
                if args[0].startswith("{") and args[0].endswith("}"):
                    file = os.path.abspath(info.get_path_with_lib(ofile := args[0][1:-1]))
                    search_path = "_std"
                else:
                    if name != "__main__":
                        file = os.path.join(os.path.dirname(name), args[0])
                    search_path = "_loc"
                if mod_s.c_import(nframe, file, search_path, loc="."):
                    print(f"luaj: Something wrong happened...\nLine {lpos}\nFile {name}")
                    return error.PREPROCESSING_ERROR
            elif ins == "use:c" and argc == 3 and args[1] == "as":
                if args[0].startswith("{") and args[0].endswith("}"):
                    file = os.path.abspath(info.get_path_with_lib(ofile := args[0][1:-1]))
                    search_path = "_std"
                else:
                    if name != "__main__":
                        file = os.path.join(os.path.dirname(name), args[0])
                    search_path = "_loc"
                if mod_s.c_import(nframe, file, search_path, loc=".", alias=args[2]):
                    print(f"luaj: Something wrong happened...\nLine {lpos}\nFile {name}")
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
            ins, *args = group(line)
            if ins == "return" and any(is_reference_var(x) for x in args):
                error.error(lpos, file, "Return statement returns a reference!")
                return error.TYPE_ERROR
            try:
                args = nest_args(exprs_preruntime(args))
            except:
                error.error(lpos, file, "Line has an imballance in parenthesis!")
                return error.SYNTAX_ERROR
            res.append((lpos, name, ins, args))
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
            entire_line = line_pos, file, ins, args = nres[pos]
            argc = len(args)
            if ins == "switch::static":
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
                    line_pos, file, ins, args = switch_block[sub_pos]

                    if ins == "case" and len(args) == 1:
                        if not is_static(args[0]):
                            error.warning(line_pos, file, f"Expression {args[0]!r} is not a constant. Use `switch` instead!")
                        temp = get_block(switch_block, sub_pos)
                        if temp is None:
                            error.error(line_pos, file, f"Switch statement is invalid! For case '{args[0]}'")
                            return error.PREPROCESSING_ERROR
                        sub_pos, body[process_arg(nframe, args[0])] = temp
                    elif ins == "default" and not args:
                        temp = get_block(switch_block, sub_pos)
                        if temp is None:
                            error.error(line_pos, file, f"Switch statement is invalid! For case '{args[0]}'")
                            return error.PREPROCESSING_ERROR
                        sub_pos, body[None] = temp
                    else:
                        error.error(line_pos, file, f"Switch statement is invalid!")
                        return error.SYNTAX_ERROR
                    sub_pos += 1
                res.append([og_lpos, file, "_intern.switch::static", [body, arg_val]])
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
                    line_pos, file, ins, args = switch_block[sub_pos]

                    if ins == "case" and len(args) == 1:
                        temp = get_block(switch_block, sub_pos)
                        if temp is None:
                            error.error(line_pos, file, f"Switch statement is invalid! For case '{args[0]}'")
                            return error.PREPROCESSING_ERROR
                        sub_pos, tbody = temp
                        opts.append({
                            "value": args[0],
                            "body": tbody
                        })
                    elif ins == "default" and not args:
                        temp = get_block(switch_block, sub_pos)
                        if temp is None:
                            error.error(line_pos, file, f"Switch statement is invalid! For case '{args[0]}'")
                            return error.PREPROCESSING_ERROR
                        sub_pos, body["default"] = temp
                    else:
                        error.error(line_pos, file, "Invalid switch statement!")
                        return error.PREPROCESSING_ERROR
                    sub_pos += 1
                res.append([og_lpos, file, "_intern.switch::dynamic", [body, arg_val]])
            elif ins == "fn::inline" and argc == 2:
                inline_name, param = process_args(nframe, args)
                temp = get_block(nres, pos)
                if temp is None:
                    error.error(line_pos, file, "Inline function statement is invalid!")
                    return error.PREPROCESSING_ERROR
                pos, inlines[f"{inline_name}"] = temp[0], {
                    "args": param,
                    "body": temp[1]
                }
            elif ins == "fn::static" and argc == 2:
                function_name, params = args
                temp_block = get_block(nres, pos)
                if temp_block is None:
                    break
                else:
                    pos, body = temp_block
                func = objects.make_function(constants.nil, function_name, body, process_args(nframe, params))
                rset(nframe[-1], function_name, func)
                func["capture"] = nframe[-1] # automatically store the scope it was defined in
            elif ins == "string::static" and argc == 1:
                name = process_arg(nframe, args[0])
                temp = get_block(nres, pos)
                if temp is None:
                    error.error(line_pos, file, "Static string statement is invalid!")
                    return error.PREPROCESSING_ERROR
                pos, block = temp
                lines = []
                og_line = line_pos
                og_file = file
                for [line_pos, file, ins, args] in block:
                    if len(args) > 1:
                        error.error(line_pos, file, f"Invalid line length!")
                        return error.PREPROCESSING_ERROR
                    args = process_args(nframe, args)
                    if ins == ".":
                        lines.append((args[0] if args else "")+"\n")
                    elif ins == "+":
                        lines.append(args[0] if args else "")
                    else:
                        error.error(line_pos, file, f"Invalid operator length!")
                        return error.PREPROCESSING_ERROR
                rset(nframe[-1], name, "".join(lines))
            elif ins.startswith("inline::") and argc == 1:
                name = ins[8:]
                if name in inlines:
                    res.extend(process_inline(args[0], inlines[name]))
                else:
                    error.error(line_pos, file, f"Invalid inline function: {name}")
                    return error.PREPROCESSING_ERROR
            else:
                if args and preprocessing_flags["EXPRESSION_FOLDING"]:
                    res.append((line_pos, file, ins, to_static(args, env=nframe)))
                else:
                    res.append(entire_line)
            pos += 1
        frame = {
            "code": res,      # HLIR or LLIR code
            "frame": nframe,  # Stack frame, populated via modules
                              # Is the code HLIR or LLIR?
                              # This will be used in the future
                              # to automatically switch execution functions.
            "llir": False,
        }
        if preprocessing_flags["EXPERIMENTAL_LLIR"]:
            if process_hlir is None:
                raise Exception("process_hlir function not available!\nFlag '-use-parser2' wasnt suplied!")
            process_hlir(frame)
        return frame
    return error.PREPROCESSING_ERROR

@objects.register_run_fn
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
                        error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][3][0]}")
                        raise error.DPLError(error.RUNTIME_ERROR)
                if variadic:
                    variadic.append(value)
                elif line_position >= function_obj["variadic"]["index"]:
                    variadic.append(value)
                else:
                    frame[-1][name] = value
            frame[-1][function_obj["variadic"]["name"]] = variadic
        else:
            error.error(line_position, module_filepath, f"Function {function_obj['name']} is a variadic and requires {function_obj['variadic']['index']+1} arguments or more.")
            raise error.DPLError(error.RUNTIME_ERROR)
    else:
        if len(args) != len(function_obj["args"]) and not function_obj["defaults"]:
            text = "more" if len(args) > len(function_obj["args"]) else "less"
            error.error(line_position, module_filepath, f"Function got {text} than expected arguments!\nExpected {len(function_obj['args'])} arguments but got {len(args)} arguments.")
            raise error.DPLError(error.RUNTIME_ERROR)
        for n, v in function_obj["defaults"].items():
            frame[-1][n] = v
        for name, value in itertools.zip_longest(function_obj["args"], args, fillvalue=constants.nil):
            if name == constants.nil:
                break
            if name in function_obj["checks"]:
                if not run_func(frame, function_obj["checks"][name], value):
                    error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][3][0]}")
                    raise error.DPLError(error.RUNTIME_ERROR)
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

    instruction_pointer = 0
    code_length = len(code)

    while instruction_pointer < code_length:
        line_position, module_filepath, ins, oargs = code[instruction_pointer]

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
        if ins == "inc" and argc == 1:
            rset(frame[-1], args[0], rget(frame[-1], args[0], default=0) + 1)
        elif ins == "dec" and argc == 1:
            rset(frame[-1], args[0], rget(frame[-1], args[0], default=0) - 1)
        elif ins == "setref" and argc == 3 and args[1] == "=":
            reference, _, value = args
            if reference["scope"] >= len(frame) or reference["scope_uuid"] != frame[reference["scope"]]["_scope_uuid"]:
                error.error(line_position, module_filepath, f"Reference for {reference['name']} is invalid and may have outlived its original scope!")
                return error.REFERENCE_ERROR
            rset(frame[reference["scope"]], reference["name"], value)
            reference["value"] = value
        elif ins == "sleep" and argc == 1 and isinstance(args[0], (int, float)):
            time.sleep(args[0])
        elif ins == "fn" and argc >= 2:
            function_name, params, *tags = args
            temp_block = get_block(code, instruction_pointer)
            if temp_block is None:
                break
            else:
                instruction_pointer, body = temp_block
            func = objects.make_function(frame[-1], function_name, body, process_args(frame, params))
            entry_point = False
            if function_name.endswith("::entry_point"):
                entry_point = True
            for tag in tags:
                if tag == "entry_point":
                    entry_point = True
                if isinstance(tag, str):
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
            rset(frame[-1], function_name, func)

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
        elif ins == "check" and argc == 2:
            name, body = args
            fn = make_function(frame[-1], name, [(0, "::internal", "return", [Expression(body)])], ("self",))
            rset(frame[-1], name, fn)
        elif ins == "use" and argc == 1:
            if args[0].startswith("{") and args[0].endswith("}"):
                f = os.path.abspath(info.get_path_with_lib(ofile := args[0][1:-1]))
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
        elif ins == "use" and argc == 3 and args[1] == "as":
            if args[0].startswith("{") and args[0].endswith("}"):
                f = os.path.abspath(info.get_path_with_lib(ofile := args[0][1:-1]))
                search_path = "_std"
            else:
                f = os.path.join(os.path.dirname(name), (ofile := args[0]))
                if name != "__main__":
                    f = os.path.join(os.path.dirname(name), f)
                search_path = "_loc"
            if not os.path.exists(f):
                error.error(lpos, module_filepath, f"Not found while including: {f}")
                return error.PREPROCESSING_ERROR
            if mod_s.py_import(frame, f, search_path, loc=os.path.dirname(module_filepath), alias=args[2]):
                print(f"python: Something wrong happened...\nLine {line_position}\nFile {module_filepath}")
                return error.RUNTIME_ERROR
        elif ins == "use_luaj" and argc == 1:
            if args[0].startswith("{") and args[0].endswith("}"):
                f = os.path.abspath(info.get_path_with_lib(ofile := args[0][1:-1]))
                search_path = "_std"
            else:
                f = os.path.join(os.path.dirname(name), (ofile := args[0]))
                if name != "__main__":
                    f = os.path.join(os.path.dirname(name), f)
                search_path = "_loc"
            if not os.path.exists(f):
                error.error(lpos, module_filepath, f"Not found while including: {f}")
                return error.PREPROCESSING_ERROR
            if mod_s.luaj_import(frame, f, search_path, loc=os.path.dirname(module_filepath)):
                print(f"python: Something wrong happened...\nLine {line_position}\nFile {module_filepath}")
                return error.RUNTIME_ERROR
        elif ins == "_intern.switch::static" and argc == 2:
            temp_body = args[0].get(args[1], args[0][None])
            if not temp_body:
                instruction_pointer += 1
                continue
            if err:=execute(temp_body, frame):
                error.error(line_position, module_filepath, f"Error in switch block '{args[1]}'")
                return err
        elif ins == "_intern.switch::dynamic" and argc == 2:
            blocks, arg = args
            for block in blocks["opts"]:
                if process_arg(frame, block["value"]) == arg:
                    if (err:=execute(block["body"], frame)):
                        if err > 0:
                            error.error(line_position, module_filepath, f"Error in switch case {block['value']}: [{err}] {error.ERRORS_DICT.get(err, '???')}")
                        return err
                    break
            else:
                if (err:=execute(blocks["default"], frame)):
                    if err > 0:
                        error.error(line_position, module_filepath, f"Error in switch case {block['value']}: [{err}] {error.ERRORS_DICT.get(err, '???')}")
                    return err
        elif ins == "if" and argc == 1:
            temp_block = get_block(code, instruction_pointer)
            if temp_block is None:
                break
            else:
                instruction_pointer, body = temp_block
            if args[0]:
                err = execute(body, frame=frame)
                if err:
                    return err
        elif ins == "ifmain" and argc == 0:
            temp_block = get_block(code, instruction_pointer)
            if temp_block is None:
                break
            else:
                instruction_pointer, body = temp_block
            if module_filepath == "__main__":
                err = execute(body, frame=frame)
                if err:
                    return err
        elif ins == "match" and argc == 1:
            temp_block = get_block(code, instruction_pointer)
            if temp_block is None:
                break
            else:
                instruction_pointer, body = temp_block
            if (err := parse_match(frame, body, args[0])) > 0:
                return err
        elif ins == "get_time" and argc == 1:
            rset(frame[-1], args[0], time.time())
        elif ins == "_intern.get_index" and argc == 1:
            frame[-1][args[0]] = instruction_pointer
        elif ins == "_intern.jump" and argc == 1:
            instruction_pointer = args[0]
        elif ins == "_intern.jump" and argc == 2:
            if args[1]: instruction_pointer = args[0]
        elif ins == "for" and argc == 3 and args[1] == "in":
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            if body:
                name, _, iter = args
                index = None
                if isinstance(name, tuple):
                    index, name = name
                    iter = enumerate(iter)
                for i in iter:
                    if index is not None:
                        frame[-1][index], i = i
                    frame[-1][name] = i
                    err = execute(body, frame)
                    if err:
                        if err == error.STOP_RESULT:
                            break
                        elif err == error.SKIP_RESULT:
                            continue
                        return err
        elif ins == "enum" and argc == 1:
            name = args[0]
            names = set()
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            for _, _, ins, _ in body:
                names.add(ins)
            tmp = frame[-1][name] = {}
            for n in names:
                tmp[n] = f"enum:{module_filepath}:{name}:{n}"
        elif ins == "loop" and argc == 0:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            if body:
                while True:
                    err = execute(body, frame)
                    if err:
                        if err == error.STOP_RESULT:
                            break
                        elif err == error.SKIP_RESULT:
                            continue
                        return err
        elif ins == "dump_scope" and argc == 0:
            pprint(frame[-1])
        elif ins == "dump_vars" and argc == 1 and isinstance(args[0], dict):
            pprint(args[0], hide=False)
        elif ins == "dump_vars_fancy" and argc == 1:
            pprint({args[0]: rget(frame[-1], args[0])}, hide=False)
        elif ins == "get_time" and argc == 1:
            frame[-1][args[0]] = time.time()
        elif ins == "loop" and argc == 1:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            if body:
                for _ in range(args[0]):
                    err = execute(body, frame)
                    if err:
                        if err == error.STOP_RESULT:
                            break
                        elif err == error.SKIP_RESULT:
                            continue
                        return err
        elif ins == "while" and argc == 1:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            if isinstance(args[0], (tuple, list)):
                expr = Expression(args[0])
            else:
                expr = args[0]
            if body:
                while evaluate(frame, expr):
                    err = execute(body, frame)
                    if err:
                        if err == error.STOP_RESULT:
                            break
                        elif err == error.SKIP_RESULT:
                            continue
                        return err
        elif ins == "check_schema" and argc == 3:
            data, as_, schema = args
            if not type_checker.check_schema(data, schema):
                error.error(line_position, module_filepath, "Data doesnt comply with schema!")
                return error.TYPE_ERROR
        elif ins == "stop" and argc == 0:
            return error.STOP_RESULT
        elif ins == "skip" and argc == 0:
            return error.SKIP_RESULT
        elif ins == "exec" and argc == 3:
            if err:=run(process_code(args[0], name=args[1]), frame=args[2]):
                return err
        elif ins == "sexec" and argc == 4:
            error.silent()
            frame[-1][args[0]] = execute(process_code(args[1], name=args[2]), frame=args[3])
            error.active()
        elif ins == "fallthrough" and argc == 0:
            return error.FALLTHROUGH
        elif ins == "set" and argc == 3 and args[1] == "=":
            if args[0] != "_":
                if isinstance(args[0], (tuple, list)):
                    for name, value in zip(args[0], args[2]):
                        rset(frame[-1], name, value)
                else:
                    rset(frame[-1], args[0], args[2])
        elif ins == "mset" and argc == 3 and args[1] == "=":
            if args[0] != "_":
                if isinstance(args[0], (tuple, list)):
                    for name, value in zip(args[0], args[2]):
                        rset(frame[-1], name, value, meta=True)
                else:
                    rset(frame[-1], args[0], args[2], meta=True)
        elif ins == "del" and argc >= 1:
            for name in args:
                rpop(frame[-1], name)
        elif ins == "object" and argc == 1:
            rset(frame[-1], args[0], objects.make_object(args[0], frame))
        elif ins == "new" and argc == 2:
            object_scope, object_name = args
            if object_scope == constants.nil:
                error.error(line_position, module_filepath, f"Unknown object")
                break
            obj = copy(object_scope)
            for name, value in obj.items():
                if isinstance(value, objects.function_type):
                    value["self"] = obj
            obj["_instance_name"] = object_name
            rset(frame[-1], object_name, obj)
        elif ins == "make_cons" and argc == 1:
            attrs = list(name for name, value in args[0].items() if not name.startswith("_") and not isinstance(value, objects.function_type))
            func = objects.make_method("new", [
                (line_position, f"{module_filepath}:internal", "new", [":self", "tmp"]),
                *[
                    (line_position, f"{module_filepath}:internal", "set", [f"tmp.{name}", "=", f":{name}"])
                    for name in attrs
                ],
                (line_position, f"{module_filepath}:internal", "return", [":tmp"]),
            ] , attrs, args[0])
            args[0]["new"] = func
        elif ins == "method" and argc >= 2:
            name, params = args
            scope_name, method_name = name.rsplit(".", 1)
            self = rget(frame[-1], scope_name)
            if self == constants.nil:
                error.error(
                    line_position, module_filepath, "Cannot bind a method to a value that isnt a scope!"
                )
                return error.RUNTIME_ERROR
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            func = objects.make_method(frame[-1], method_name, body, process_args(frame, params), self)
            self[method_name] = func
        elif ins == "benchmark" and argc == 2:
            times, var_name = args
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            instruction_pointer, body = temp
            deltas = []
            # run once to check time
            # to decide whether to use threads or not
            start = time.perf_counter()
            if (err:=execute(body, frame)) > 0:
                error.error(line_position, module_filepath, f"Benchmark raised an error: [{err}] {error.ERRORS_DICT.get(err, '???')}")
                return err
            first_delta = time.perf_counter() - start
            dlock = threading.Lock()
            use_thread = False
            # if more than once, and takes more than 10 seconds
            if times < 3 and first_delta[0] > 10 and first_delta[1] == "s":
                use_thread = True
            if use_thread:
                for _ in range(times):
                    def th():
                        start = time.perf_counter()
                        if (err:=execute(body, frame)) > 0:
                            error.error(line_position, module_filepath, f"Benchmark raised an error: [{err}] {error.ERRORS_DICT.get(err, '???')}")
                            return err
                        delta = time.perf_counter() - start
                        with dlock:
                            deltas.append(delta)
                    tht = threading.Thread(target=th)
                    tht.deamon = True
                    tht.start()
            else:
                for _ in range(times):
                    start = time.perf_counter()
                    if (err:=execute(body, frame)) > 0:
                        error.error(line_position, module_filepath, f"Benchmark raised an error: [{err}] {error.ERRORS_DICT.get(err, '???')}")
                        return err
                    delta = time.perf_counter() - start
                    deltas.append(delta)
            ct, unit = utils.convert_sec(sum(deltas)/len(deltas))
            rset(frame[-1], var_name, (ct, unit))
        elif ins == "inherit" and argc == 5 and args[1] == "from" and args[3] == "for":
            attrs, _, parent, _, child = args
            if attrs == "all":
                for attr in parent:
                    if attr.startswith("_"):
                        continue
                    val = copy(rget(parent, attr))
                    if isinstance(val, objects.function_type):
                        val["self"] = child
                    rset(child, attr, val)
            else:
                for attr in attrs:
                    if attr in parent:
                        val = copy(rget(parent, attr))
                        if isinstance(val, objects.function_type):
                            val["self"] = child
                        rset(child, attr, val)
        elif ins == "START_TIME" and argc == 0:
            start_time = time.perf_counter()
        elif ins == "STOP_TIME" and argc == 0:
            end_time = time.perf_counter() - start_time
        elif ins == "LOG_TIME" and argc == 0:
            ct, unit = utils.convert_sec(time.perf_counter() - start_time)
            error.info(f"Elapsed time: {ct:,.8f}{unit}")
        elif ins == "LOG_TIME" and argc == 1:
            ct, unit = utils.convert_sec(time.perf_counter() - start_time)
            error.info(f"Elapsed time: {args[0]} {ct:,.8f}{unit}")
        elif ins == "cmd" and argc == 1:
            os.system(args[0])
        elif ins == "cmd" and argc == 2:
            frame[-1][args[1]] = os.system(args[0])
        elif ins == "pass":
            ...
        elif ins == "exit" and argc == 0:
            sys.exit()
        elif ins == "exit" and argc == 1:
            sys.exit(args[0])
        elif ins == "return":  # Return to the latched names
            if any(isinstance(x, objects.reference_type) for x in args):
                error.error(line_position, module_filepath, "Function returned a reference, perhaps they were supposed to be dereferenced?")
                return error.TYPE_ERROR
            if (latched_names := rget(frame[-1], "_returns")) != constants.nil:
                if latched_names == "_":
                    return error.STOP_FUNCTION
                if len(latched_names) == 1:
                    rset(
                        frame[-1]["_nonlocal"],
                        latched_names[0],
                        args[0]
                            if isinstance(args, (tuple, list))
                            and len(args) == 1
                        else args)
                else:
                    for name, value in zip(latched_names, args):
                        rset(frame[-1]["_nonlocal"], name, value)
            return error.STOP_FUNCTION
        elif ins == "catch" and argc == 3:  # catch return value of a function
            rets, func_name, args = args
            if (function_obj := rget(frame[-1], func_name, default=rget(frame[0], func_name))) == constants.nil or not isinstance(function_obj, dict):
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
                                error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][3][0]}")
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
                            error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][3][0]}")
                            return error.RUNTIME_ERROR
                    frame[-1][name] = value
            frame[-1]["_returns"] = rets
            err = execute(function_obj["body"], frame)
            if err > 0:
                error.error(line_position, module_filepath, f"Error in function {ins!r}")
                return err
            pscope(frame)
        elif ins == "safe" and argc == 5 and args[0] == "catch":  # catch return value of a function
            _, ecode, rets, func_name, args = args
            if (function_obj := rget(frame[-1], func_name, default=rget(frame[0], func_name))) == constants.nil or not isinstance(function_obj, dict):
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
                                error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][3][0]}")
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
                            error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][3][0]}")
                            return error.RUNTIME_ERROR
                    frame[-1][name] = value
            frame[-1]["_returns"] = rets
            error.silent()
            err = execute(function_obj["body"], frame)
            error.active()
            pscope(frame)
            if err > 0:
                frame[-1][ecode] = err
        elif ins == "safe" and argc == 3:  # catch return value of a function
            ecode, func_name, args = args
            if (function_obj := rget(frame[-1], func_name, default=rget(frame[0], func_name))) == constants.nil or not isinstance(function_obj, dict):
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
                                error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][3][0]}")
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
                            error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][3][0]}")
                            return error.RUNTIME_ERROR
                    frame[-1][name] = value
            error.silent()
            err = execute(function_obj["body"], frame)
            error.active()
            pscope(frame)
            if err > 0:
                frame[-1][ecode] = err
        elif ins == "DEFINE_ERROR" and 0 < argc < 3:
            error.register_error(*args)
        elif ins == "ecatch" and argc == 3:  # catch return value of a python function
            rets, name, args = args
            args = process_args(frame, args)
            if (function := rget(frame[-1], name, default=rget(frame[0], name))) == constants.nil or not hasattr(function, "__call__"):
                error.error(line_position, module_filepath, f"Invalid function {name!r}!")
                return error.NAME_ERROR
            try:
                func_params = mod_s.get_py_params(function)[2:]
                if func_params and any(map(lambda x: x.endswith("_body") or x.endswith("_xbody"), func_params)):
                    t_args = []
                    for i, _ in zip(func_params, args):
                        if i.endswith("_xbody"):
                            temp = get_block(code, instruction_pointer, start=0)
                            if temp is None:
                                error.error(line_position, module_filepath, f"Function '{function.__name__}' expected a block!")
                                return (error.RUNTIME_ERROR, error.SYNTAX_ERROR)
                            instruction_pointer, body = temp
                            t_args.append(body)
                        elif i.endswith("_body"):
                            temp = get_block(code, instruction_pointer)
                            if temp is None:
                                error.error(line_position, module_filepath, f"Function '{function.__name__}' expected a block!")
                                return (error.RUNTIME_ERROR, error.SYNTAX_ERROR) # say "runtime error" caised by "syntax error"
                            instruction_pointer, body = temp
                            t_args.append(body)
                        else:
                            t_args.append(args.pop(0))
                else:
                    t_args = args
                res = mod_s.call(
                    function, frame, meta_attributes["internal"]["main_path"], t_args
                )
                if (
                    res is None
                    and info.WARNINGS
                    and is_debug_enabled("warn_no_return")
                ):
                    error.warn(
                        "Function doesnt return anything. To reduce overhead please dont use pycatch.\nLine {line_position}\nFile {module_filepath}"
                    )
                if isinstance(res, tuple):
                    if rets != "_":
                        for name, value in zip(rets, res):
                            rset(frame[-1], name, value)
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
        elif ins == "dict" and argc == 1:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            if parse_dict(frame, args[0], body):
                break
        elif ins == "string" and argc == 1:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            if parse_string(frame, args[0], body):
                break
        elif ins == "string" and argc == 2 and args[1] == "new_line":
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            if parse_string(frame, args[0], body, True):
                break
        elif ins == "string" and argc == 4 and args[1] == "new_line" and args[2] == "as":
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            if parse_string(frame, args[0], body, True, args[3]):
                break
        elif ins == "list" and argc == 1:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            if parse_list(frame, args[0], body):
                break
        elif ins == "struct" and argc == 1:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            if parse_struct(frame, mod_s.global_ffi, args[0], body):
                break
        elif ins == "struct" and argc == 4 and args[2] == "as":
            struct, args, _, name = args
            args = process_args(frame, args)
            rset(frame[-1], name, mod_s.global_ffi.new(struct, args))
        elif ins == "raise" and isinstance(args[0], int) and argc == 2:
            error.error(line_position, module_filepath, args[1])
            return args[0]
        elif ins == "raise" and isinstance(args[0], int) and argc == 1:
            error.error(line_position, module_filepath, f"Error [{args[0]}]: {error.ERRORS_DICT.get(args[0], '???')}")
            return args[0]
        elif (
            (function_obj := rget(frame[-1], ins, default=rget(frame[0], ins)))
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
                                error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][3][0]}")
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
                for name, value in itertools.zip_longest(function_obj["args"], args, fillvalue=constants.nil):
                    if name == constants.nil:
                        break
                    if name in function_obj["checks"]:
                        if not run_func(frame, function_obj["checks"][name], value):
                            error.error(line_position, module_filepath, f"Argument {name!r} ({value!r}) of function {function_obj['name']} does not pass check {function_obj['checks'][name]['body'][0][3][0]}")
                            return error.RUNTIME_ERROR
                    frame[-1][name] = value
            if function_obj["capture"] != constants.nil:
                frame[-1]["_capture"] = function_obj["capture"]
            err = execute(function_obj["body"], frame)
            if err and err != error.STOP_FUNCTION:
                if err > 0: error.error(line_position, module_filepath, f"Error in function {ins!r}: [{err}] {error.ERRORS_DICT.get(err, '???')}")
                return err
            pscope(frame)
        elif (
            function := rget(frame[-1], ins, default=rget(frame[0], ins))
        ) != constants.nil and hasattr(
            function, "__call__"
        ):  # call a python function

            # Even I dont under stand this now...
            # good luck future me
            args = process_args(frame, args[0])
            try:
                func_params = mod_s.get_py_params(function)[2:]
                if func_params and any(map(lambda x: x.endswith("_body") or x.endswith("_xbody"), func_params)):
                    t_args = []
                    for i, _ in zip(func_params, args):
                        if i.endswith("_xbody"):
                            temp = get_block(code, instruction_pointer, start=0)
                            if temp is None:
                                error.error(line_position, module_filepath, f"Function '{function.__name__}' expected a block!")
                                return (error.RUNTIME_ERROR, error.SYNTAX_ERROR)
                            instruction_pointer, body = temp
                            t_args.append(body)
                        elif i.endswith("_body"):
                            temp = get_block(code, instruction_pointer)
                            if temp is None:
                                error.error(line_position, module_filepath, f"Function '{function.__name__}' expected a block!")
                                return (error.RUNTIME_ERROR, error.SYNTAX_ERROR) # say "runtime error" caised by "syntax error"
                            instruction_pointer, body = temp
                            t_args.append(body)
                        else:
                            t_args.append(args.pop(0))
                else:
                    t_args = args
                res = mod_s.call(
                    function, frame, meta_attributes["internal"]["main_path"], t_args
                )
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
        elif ins == "local" and argc == 1:
            execute(args[0]["body"], frame)
        elif ins == "on_new_scope" and argc == 0:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                error.error(line_position, module_filepath, f"on_new_scope expected a block!")
                return (error.RUNTIME_ERROR, error.SYNTAX_ERROR) # say "runtime error" caised by "syntax error"
            instruction_pointer, body = temp

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
        elif ins == "on_pop_scope" and argc == 0:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                error.error(line_position, module_filepath, f"on_new_scope expected a block!")
                return (error.RUNTIME_ERROR, error.SYNTAX_ERROR) # say "runtime error" caised by "syntax error"
            instruction_pointer, body = temp

            def make_on_new_scope_fn(ons_b, parent_frame):
                def on_new_scope_tmp_fn(scope, scope_id):
                    fr = new_frame()
                    fr[0]["scope"] = scope
                    fr[0]["scope_id"] = scope_id
                    fr[0]["globals"] = parent_frame[0]
                    return execute(ons_b, fr)
                return on_new_scope_tmp_fn
            on_pop_scope.append({
                "func": make_on_new_scope_fn(body, frame),
                "from": f"dpl:{module_filepath}:{line_position}"
            })
        else:
            if not isinstance((obj := rget(frame[-1], ins)), dict) and obj in (
                None,
                constants.none,
            ):
                print(
                    "\nAdditional Info: User may have called a partially defined function!",
                    end="",
                )
            error.error(line_position, module_filepath, f"Invalid instruction {ins}")
            return error.RUNTIME_ERROR
        instruction_pointer += 1
    else:
        return 0
    error.error(line_position, module_filepath, "Error was raised!")
    return error.SYNTAX_ERROR


class IsolatedParser:
    def __init__(self, file_name="__main__", main_path=".", libdir=info.PERM_LIBDIR, argv=None):
        self.defaults = {
            "libdir": info.PERM_LIBDIR,
            "argv": info.ARGV.copy(),
            "main_file": varproc.internal_attributes["main_file"],
            "main_path": varproc.internal_attributes["main_path"],
            "meta": copy(varproc.meta_attributes),
        }
        varproc.internal_attributes["main_file"] = file_name
        varproc.internal_attributes["main_path"] = main_path
        info.LIBDIR = libdir

    def __enter__(self):
        return self

    def run_code(self, code, frame=None):
        if isinstance(code, str):
            code = process_code(code)
        return run_code(code, frame=frame)

    def __exit__(self, exc, exc_ins, tb):
        info.LIBDIR = self.defaults["libdir"]
        info.ARGV = self.defaults["argv"]
        varproc.internal_attributes["main_file"] = self.defaults["main_file"]
        varproc.internal_attributes["main_path"] = self.defaults["main_path"]
        varproc.meta_attributes.update(self.defaults["meta"])
        return False


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
        is_llir = code["llir"]
        code, nframe = code["code"], code["frame"]
    elif isinstance(code, list):
        return execute(code, frame)
    else:
        is_llir = False
        nframe = new_frame()
    if frame is not None:
        frame[0].update(nframe[0])
    else:
        frame = nframe
    
    # the process_code function returned
    # LLIR? Run it using py_parser2
    # even if theres no flag.
    # This if some d*ckhead
    # somehow injects LLIR into
    # this function. Or when Im too
    # lazy and do tests directly with this.
    if is_llir:
        if pp2_execute is None:
            raise Exception("Execution function for llir isnt available\nImport py_parser2 not py_parser to use this feature!")
        return pp2_execute(code, frame)
    
    # Run using old parser
    # the function below is recursive
    # thats why depth was mentioned
    # in the doc string.
    try:
        return execute(code, frame)
    except error.DPLError as e:
        return e.code
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

if "get-internals" in info.program_flags:
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

mod_s.dpl.execute = execute_code
mod_s.dpl.call_dpl = run_func

# Some of the functions here have been turned into decorators
