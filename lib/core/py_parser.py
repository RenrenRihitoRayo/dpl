# Parser and Preprocessor
# The heart, the interpreter of DPL
# will coexist beside py_parser2 cuz why not
# makes sure HLIR can still be executed
# directly

import time
import itertools
import dill
from copy import deepcopy as copy
from . import py_argument_handler
arguments_handler = py_argument_handler.arguments_handler
from .runtime import *
from . import utils
from . import objects
from . import constants
from . import info
import traceback
import sys
import os

pp2_execute = None
process_hlir = None

def register_execute(func):
    global pp2_execute
    pp2_execute = func

def register_process_hlir(func):
    global process_hlir
    process_hlir = func

def get_block(code, current_p, supress=False, start=1):
    "Get a code block. Runtime! (helps init become faster)"
    instruction_pointer = current_p + 1
    pos, file, ins, _ = code[instruction_pointer]
    k = start
    if k == 0 and ins not in info.INCREAMENTS:
        error.error(pos, file, "Expected to have started with an instruction that indents.")
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
            print(f"Error in line {pos} file {file!r}\nCause: Block wasnt closed!")
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
    if isinstance(d, list):
        for i in d:
            if isinstance(i, list):
                print("  "*l+"[")
                pprint(i, l+1, seen)
                print("  "*l+"]")
            elif isinstance(i, dict):
                print("  "*l+"{")
                pprint(i, l+1, seen)
                print("  "*l+"}")
            else:
                print("  "*l+repr(i))
        return
    elif not isinstance(d, dict):
        print("  "*l+repr(d))
        return
    if not d:
        print("{}")
    for name, value in d.items():
        if isinstance(name, str) and name.startswith("_") and hide:
            ...
        elif isinstance(value, dict):
            print("  "*l+f"{name!r} => {{")
            pprint(value, l+1, seen)
            print("  "*l+"}")
        elif isinstance(value, list):
            print("  "*l+f"{name!r} => [")
            pprint(value, l+1, seen)
            print("  "*l+"]")
        else:
            print("  "*l+f"{name!r} = {value!r}")

def process(fcode, name="__main__"):
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
        line = line.replace("!__line__", str(lpos))
        line = line.replace("!__file__", name if name != "__main__" else meta_attributes["internal"]["main_file"])
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
                    res.extend(process(f.read(), name=name))
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
                (vars, cccc) = me
                nframe[0].update(vars)
                res.extend(cccc)
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
                error.pre_error(
                    lpos, name, f"{name!r}:{lpos}: Invalid directive {ins!r}"
                )
                break
        else:
            ins, *args = group(line)
            args = nest_args(exprs_preruntime(args))
            if preprocessing_flags["EXPRESSION_FOLDING"]: args = to_static(nframe,
                args
            )  # If there are static parts in the arguments run them before runtime.
            res.append((lpos, name, ins, args if len(args) else None))
    else:
        if multiline:
            error.pre_error(
                last_comment,
                name,
                f"{name!r}:{last_comment}: Unclosed multiline comment!",
            )
            return error.PREPROCESSING_ERROR
#        nres = []
# temporary!
#        if preprocessing_flags["DEAD_CODE_OPT"]:
#            instruction_pointer = 0
#            warn_num = 0
#            nres = []
#            while instruction_pointer < len(res):
#                line = line_pos, file, ins, args = res[instruction_pointer]
#                if args is None:
#                    args = []
#                if (
#                    ins in {"for", "loop", "while"}
#                    and instruction_pointer + 1 < len(res)
#                    and res[instruction_pointer + 1][2] in {"end", "stop", "skip"}
#                ):
#                    if preprocessing_flags["WARNINGS"]:
#                        (error.warnf if not preprocessing_flags["STRICT"] else error.error)(
#                            line_pos, file,
#                            f"{ins!r} statement is empty!"
#                        )
#                        if preprocessing_flags["STRICT"]:
#                            return error.PREPROCESSING_ERROR
#                    temp = get_block(res, instruction_pointer)
#                    if temp:
#                        instruction_pointer, _ = temp
#                    else:
#                        return []
#                    warn_num += 1
#                elif (
#                    ins in {"if", "module", "body"}
#                    and instruction_pointer + 1 < len(res)
#                    and res[instruction_pointer + 1][2] == "end"
#                ):
#                    if preprocessing_flags["WARNINGS"]:
#                        (error.warnf if not preprocessing_flags["STRICT"] else error.error)(
#                            line_pos, file,
#                            f"{ins!r} statement is empty!"
#                        )
#                        if preprocessing_flags["STRICT"]:
#                            return error.PREPROCESSING_ERROR
#                    temp = get_block(res, instruction_pointer)
#                    if temp:
#                        instruction_pointer, _ = temp
#                    else:
#                        return []
#                    warn_num += 1
#                elif (
#                    ins in {"case", "match", "with", "default"}
#                    and instruction_pointer + 1 < len(res)
#                    and res[instruction_pointer + 1][2] in {"end", "return"}
#                ):
#                    if ins != "default" and len(args) == 0:
#                        error.error(
#                            line_pos, file,
#                            f"Error: Malformed {ins!r} statement/sub-statements!\nLine {line_pos}\nIn file {file!r}"
#                        )
#                        return error.PREPROCESSING_ERROR
#                    if preprocessing_flags["WARNINGS"]:
#                        (error.warnf if not preprocessing_flags["STRICT"] else error.error)(
#                            line_pos, file,
#                            f"{ins!r} statement is empty!"
#                        )
#                        if preprocessing_flags["STRICT"]:
#                            return error.PREPROCESSING_ERROR
#                    temp = get_block(res, instruction_pointer)
#                    if temp:
#                        instruction_pointer, _ = temp
#                    else:
#                        return []
#                    warn_num += 1
#                elif (
#                    ins in {"fn", "method"}
#                    and instruction_pointer + 1 < len(res)
#                    and res[instruction_pointer + 1][2] in {"end", "return"}
#                ):
#                    if res[instruction_pointer + 1][2] == "return" and len(res[instruction_pointer + 1][3]) != 0:
#                        nres.append(line)
#                        instruction_pointer += 1
#                        continue
#                    if len(args) == 0:
#                        error.warn(
#                            f"Error: Malformed function definition!\nLine {line_pos}\nIn file {file!r}"
#                        )
#                        return error.PREPROCESSING_ERROR
#                    if preprocessing_flags["WARNINGS"]:
#                        (error.warnf if not preprocessing_flags["STRICT"] else error.error)(
#                            line_pos, file,
#                            f"{ins!r} statement is empty!"
#                        )
#                        if preprocessing_flags["STRICT"]:
#                            return error.PREPROCESSING_ERROR
#                    temp = get_block(res, instruction_pointer)
#                    if temp:
#                        instruction_pointer, _ = temp
#                    else:
#                        return []
#                    warn_num += 1
#                else:
#                    nres.append(line)
#                instruction_pointer += 1
#            if preprocessing_flags["WARNINGS"] and warn_num:
#                print(f"Warning Info: {warn_num:,} Total warnings.")
#        else:
#            nres = res
        # pass for switches
        nres = res
        res = []
        offset = 0
        whole_offset = 0
        for instruction_pointer, [line_pos, file, ins, args] in enumerate(nres):
            # compile the switch statement
            # this uses _intern.switch
            if ins == "switch" and len(args) == 1:
                body = {None:[]}
                arg_val = args[0]
                og_lpos = line_pos
                temp = get_block(nres, instruction_pointer)
                if temp is None:
                    error.error(line_pos, file, "Switch statement is invalid!")
                    return error.PREPROCESSING_ERROR
                whole_offset, switch_block = temp 
                for instruction_pointer, [line_pos, _, ins, args] in enumerate(switch_block):
                    if ins == "case" and len(args) == 1:
                        temp = get_block(switch_block, instruction_pointer)
                        if temp is None:
                            error.error(line_pos, file, f"Switch statement is invalid! For case '{args[0]}'")
                            return error.PREPROCESSING_ERROR
                        offset, body[process_arg(nframe, args[0])] = temp
                    elif ins == "default" and args is None:
                        temp = get_block(switch_block, instruction_pointer)
                        if temp is None:
                            error.error(line_pos, file, f"Switch statement is invalid! For case '{args[0]}'")
                            return error.PREPROCESSING_ERROR
                        offset, body[None] = temp
                    else:
                        if instruction_pointer > offset:
                            error.error(line_pos, file, "Invalid switch statement!")
                            return error.PREPROCESSING_ERROR
                whole_offset += 1
                res.append([og_lpos, file, "_intern.switch", [body, arg_val]])
            elif instruction_pointer >= whole_offset and ins != "pass":
                res.append([line_pos, file, ins, args])
        frame = {
            "code": res,             # HLIR or LLIR code
            "frame": nframe, # Stack frame, populated via modules
            # Is the code HLIR or LLIR?
            #This will be used in the future
            # to automatically switch execution functions.
            "llir": False,
        }
        # simple in place change :D proud of this.
        if preprocessing_flags["EXPERIMENTAL_LLIR"]:
            if process_hlir is None:
                raise Exception("Process hlir function not available!\nFlag '-use-py-parser2' wasnt suplied!")
            process_hlir(frame)
        return frame
    return error.PREPROCESSING_ERROR


def execute(code, frame=None):
    """
    Low level function to run.
    Unlike the old run function
    on setup it requires less conditions
    per level of recursion.
    Run HLIR,
    Not LLIR.
    This is used internally.
    Use run instead for more logic.
    """
    
    instruction_pointer = 0
    # the contents of the new run function
    # was previously here
    if frame is None:
        frame = new_frame()
    
    while instruction_pointer < len(code):
        pos, file, ins, oargs = code[instruction_pointer]
            
        ins = process_arg(frame, ins)
        if not oargs is None:
            try:
                args = process_args(frame, oargs)
                argc = len(args)
            except Exception as e:
                raise
                error.error(
                    pos,
                    file,
                    f"Something went wrong when arguments were processed:\n{e}\n> {oargs!r}",
                )
                return error.PYTHON_ERROR
        else:
            args = []
            argc = 0
        if ins == "inc" and argc == 1:
            rset(frame[-1], args[0], rget(frame[-1], args[0], default=0) + 1)
        elif ins == "dec" and argc == 1:
            rset(frame[-1], args[0], rget(frame[-1], args[0], default=0) - 1)
        elif ins == "setref" and argc == 3 and args[1] == "=":
            reference, _, value = args
            if reference["scope"] >= len(frame) or (
            frame[reference["scope"]]["_scope_uuid"] != "disabled" and
            frame[reference["scope"]]["_scope_uuid"] != reference["scope_uuid"]):
                error.error(pos, file, f"Reference for {reference['name']} is invalid and may have outlived its original scope!")
                return error.REFERENCE_ERROR
            rset(frame[reference["scope"]], reference["name"], value)
            reference["value"] = value
        elif ins == "fn" and argc == 2:
            name, params = args
            block = get_block(code, instruction_pointer)
            if block is None:
                break
            else:
                instruction_pointer, body = block
            func = objects.make_function(name, body, params)
            rset(frame[-1], name, func)
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
                error.error(lpos, file, f"Not found while including: {f}")
                return error.PREPROCESSING_ERROR
            if mod_s.py_import(frame, f, search_path, loc=os.path.dirname(file)):
                print(f"python: Something wrong happened...\nLine {pos}\nFile {file}")
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
                error.error(lpos, file, f"Not found while including: {f}")
                return error.PREPROCESSING_ERROR
            if mod_s.py_import(frame, f, search_path, loc=os.path.dirname(file), alias=args[2]):
                print(f"python: Something wrong happened...\nLine {pos}\nFile {file}")
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
                error.error(lpos, file, f"Not found while including: {f}")
                return error.PREPROCESSING_ERROR
            if mod_s.luaj_import(frame, f, search_path, loc=os.path.dirname(file)):
                print(f"python: Something wrong happened...\nLine {pos}\nFile {file}")
                return error.RUNTIME_ERROR
        elif ins == "_intern.switch" and argc == 2:
            body = args[0].get(args[1], args[0][None])
            if not body:
                instruction_pointer += 1
                continue
            if err:=run(body, frame):
                error.error(pos, file, f"Error in switch block '{args[1]}'")
                return err
        elif ins == "if" and argc == 1:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            if args[0]:
                err = execute(body, frame=frame)
                if err:
                    return err
        elif ins == "ifmain" and argc == 0:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            if file == "__main__":
                err = execute(body, frame=frame)
                if err:
                    return err
        elif ins == "match" and argc == 1:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            if (err := parse_match(frame, body, args[0])) > 0:
                return err
        elif ins == "get_time" and argc == 1:
            frame[-1][args[0]] = time.time()
        elif ins == "_intern.get_index" and argc == 1:
            frame[-1][args[0]] = instruction_pointer
        elif ins == "_intern.jump" and argc == 1:
            instruction_pointer = args[0]
        elif ins == "_intern.jump" and argc == 2:
            if args[1]: instruction_pointer = args[0]
        elif ins == "pub" and argc >= 2 and args[0] == "fn":
            _, name, params = args
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            rset(
                frame[-1], "_export." + name, (temp:=objects.make_function(name, body, params))
            )
            rset(frame[-1], name, temp)
        elif ins == "export" and argc == 4 and args[0] == "set" and args[2] == "=":
            _, name, _, value = args
            rset(frame[-1], "_export." + name, value)
            rset(frame[-1], name, value)
#        elif ins == "tc_register" and argc == 1:
#            tc_register(args[0])
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
                tmp[n] = f"enum:{file}:{name}:{n}"
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
            if body:
                while (tmp:=evaluate(frame, args[0])):
                    err = execute(body, frame)
                    if err:
                        if err == error.STOP_RESULT:
                            break
                        elif err == error.SKIP_RESULT:
                            continue
                        return err
        elif ins == "dlopen":
            error.error(pos, file, "DEPRECATED AS OF 1.4.8 FFI IS TOO MESSY\nA REPLACEMENT WILL BE PUT IN AS SOON AS POSSIBLE")
            return error.PYTHON_ERROR
        elif ins == "dlclose":
            error.error(pos, file, "DEPRECATED AS OF 1.4.8 FFI IS TOO MESSY\nA REPLACEMENT WILL BE PUT IN AS SOON AS POSSIBLE")
            return error.PYTHON_ERROR
        elif ins == "getc":
            error.error(pos, file, "DEPRECATED AS OF 1.4.8 FFI IS TOO MESSY\nA REPLACEMENT WILL BE PUT IN AS SOON AS POSSIBLE")
            return error.PYTHON_ERROR
        elif ins == "cdef":
            error.error(pos, file, "DEPRECATED AS OF 1.4.8 FFI IS TOO MESSY\nA REPLACEMENT WILL BE PUT IN AS SOON AS POSSIBLE")
            return error.PYTHON_ERROR
        elif ins == "check_schema" and argc == 3:
            data, as_, schema = args
            if not type_checker.check_schema(data, schema):
                error.error(pos, file, "Data doesnt comply with schema!")
                return error.TYPE_ERROR
        elif ins == "stop" and argc == 0:
            return error.STOP_RESULT
        elif ins == "skip" and argc == 0:
            return error.SKIP_RESULT
        elif ins == "sched" and argc == 1:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            while time.time() < args[0]:
                pass
            err = execute(body, frame=frame)
            if err:
                return err
        elif ins == "exec" and argc == 3:
            if err:=run(process(args[0], name=args[1]), frame=args[2]):
                return err
        elif ins == "sexec" and argc == 4:
            error.silent()
            frame[-1][args[0]] = execute(process(args[1], name=args[2]), frame=args[3])
            error.active()
        elif ins == "fallthrough" and argc == 0:
            return error.FALLTHROUGH
        elif ins == "set" and argc == 3 and args[1] == "=":
            if args[0] != "_":
                if isinstance(args[0], tuple):
                    for name, value in zip(args[0], args[2]):
                        rset(frame[-1], name, value)
                else:
                    rset(frame[-1], args[0], args[2])
        elif ins == "del" and argc >= 1:
            for name in args:
                rpop(frame[-1], name)
        elif ins == "module" and argc == 1:
            name = args[0]
            temp = [frame[-1]]
            nscope(temp)
            temp[-1]["_export"] = {}
            btemp = get_block(code, instruction_pointer)
            if btemp is None:
                break
            else:
                instruction_pointer, body = btemp
            err = execute(body, temp)
            if err:
                return err
            rset(frame[-1], name, temp[1]["_export"])
            del temp
        elif ins == "object" and argc == 1:
            rset(frame[-1], args[0], objects.make_object(args[0]))
        elif ins == "new" and argc == 2:
            obj = args[0]
            if obj == constants.nil:
                error.error(pos, file, f"Unknown object")
                break
            rset(frame[-1], args[1], copy(obj))
        elif ins == "method" and argc >= 2:
            name, params = args
            sname, mname = name.rsplit(".", 1)
            self = rget(frame[-1], sname)
            if self == constants.nil:
                error.error(
                    pos, file, "Cannot bind a method to a value that isnt a scope!"
                )
                return error.RUNTIME_ERROR
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            func = objects.make_method(mname, body, params, self)
            self[mname] = func
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
            if (temp := rget(frame[-1], "_returns")) != constants.nil:
                if temp == "_":
                    return error.STOP_FUNCTION
                if len(temp) == 1:
                    rset(
                        frame[-1],
                        f"_nonlocal.{temp[0]}",
                        args[0]
                            if isinstance(args, (tuple, list))
                            and len(args) == 1
                        else args)
                else:
                    for name, value in zip(temp, args):
                        rset(frame[-1], f"_nonlocal.{name}", value)
            return error.STOP_FUNCTION
        elif ins == "catch" and argc >= 2:  # catch return value of a function
            rets, func_name, args = args
            args = process_args(frame, args)
            if (temp := rget(frame[-1], func_name, default=rget(frame[0], func_name))) == constants.nil or not isinstance(temp, dict):
                error.error(pos, file, f"Invalid function {func_name!r}!")
                break
            nscope(frame)
            if temp["capture"] != constants.nil:
                frame[-1]["_capture"] = temp["capture"]
            if temp["variadic"]["name"] != constants.nil:
                if len(args)-1 >= temp["variadic"]["index"]:
                    variadic = []
                    for pos, [name, value] in enumerate(itertools.zip_longest(temp["args"], args)):
                        if variadic:
                            variadic.append(value)
                        elif pos >= temp["variadic"]["index"]:
                            variadic.append(value)
                        else:
                            frame[-1][name] = value
                    frame[-1][temp["variadic"]["name"]] = variadic
                else:
                    error.error(pos, file, f"Function {ins} is a variadic and requires {temp['variadic']['index']+1} arguments or more.")
                    return error.RUNTIME_ERROR
            else:
                if len(args) != len(temp["args"]):
                    text = "more" if len(args) > len(temp["args"]) else "less"
                    error.error(pos, file, f"Function got {text} than expected arguments!\nExpected {len(temp['args'])} arguments but got {len(args)} arguments.")
                    return error.RUNTIME_ERROR
                for name, value in itertools.zip_longest(temp["args"], args):
                    if name is None:
                        break
                    frame[-1][name] = value
            frame[-1]["_returns"] = rets
            err = execute(temp["body"], frame)
            if err > 0:
                error.error(pos, file, f"Error in function {ins!r}")
                return err
            pscope(frame)
        elif ins == "DEFINE_ERROR" and 0 < argc < 3:
            error.register_error(*args)
        elif ins == "pycatch" and argc >= 2:  # catch return value of a python function
            rets, name, *args = args
            if (function := rget(frame[-1], name, default=rget(frame[0], name))) == constants.nil or not hasattr(function, "__call__"):
                error.error(pos, file, f"Invalid function {name!r}!")
                return error.NAME_ERROR
            try:
                if argc == 3 and isinstance(args[0], dict) and args[0].get("[RGS]"):
                    args[0].pop("[RGS]")
                    pa = args[0].pop("[PARGS]", tuple())
                    res = mod_s.call(
                        function, frame, meta_attributes["internal"]["main_path"], pa, args[0]
                    )
                else:
                    func_params = mod_s.get_py_params(function)[2:]
                    if func_params and any(map(lambda x: x.endswith("_body") or x.endswith("_xbody"), func_params)):
                        t_args = []
                        for i, _ in zip(func_params, args):
                            if i.endswith("_xbody"):
                                temp = get_block(code, instruction_pointer, start=0)
                                if temp is None:
                                    error.error(pos, file, f"Function '{function.__name__}' expected a block!")
                                    return (error.RUNTIME_ERROR, error.SYNTAX_ERROR)
                                instruction_pointer, body = temp
                                t_args.append(body)
                            elif i.endswith("_body"):
                                temp = get_block(code, instruction_pointer)
                                if temp is None:
                                    error.error(pos, file, f"Function '{function.__name__}' expected a block!")
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
                        "Function doesnt return anything. To reduce overhead please dont use pycatch.\nLine {pos}\nFile {file}"
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
                        error.error(pos, file, message)
                        return int(ecode)
            except:
                error.error(pos, file, traceback.format_exc()[:-1])
                return error.PYTHON_ERROR
        elif ins == "dict" and argc == 1:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                break
            else:
                instruction_pointer, body = temp
            if parse_dict(frame, args[0], body):
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
            error.error(pos, file, args[1])
            return args[0]
        elif (
            (temp := rget(frame[-1], ins, default=rget(frame[0], ins)))
            != constants.nil
            and isinstance(temp, dict)
            and "body" in temp and
                "args" in temp and
                "capture" in temp and
                argc == 1
            ):  # Call a function
            args = process_args(frame, args[0])
            nscope(frame)
            if temp["variadic"]["name"] != constants.nil:
                if len(args)-1 >= temp["variadic"]["index"]:
                    variadic = []
                    for pos, [name, value] in enumerate(itertools.zip_longest(temp["args"], args)):
                        if variadic:
                            variadic.append(value)
                        elif pos >= temp["variadic"]["index"]:
                            variadic.append(value)
                        else:
                            frame[-1][name] = value
                    frame[-1][temp["variadic"]["name"]] = variadic
                else:
                    error.error(pos, file, f"Function {ins} is a variadic and requires {temp['variadic']['index']+1} arguments or more.")
                    return error.RUNTIME_ERROR
            else:
                if len(args) != len(temp["args"]):
                    text = "more" if len(args) > len(temp["args"]) else "less"
                    error.error(pos, file, f"Function got {text} than expected arguments!nExpected {len(temp['args'])} arguments but got {len(args)} arguments.")
                    return error.RUNTIME_ERROR
                for name, value in itertools.zip_longest(temp["args"], args):
                    if name is None:
                        break
                    frame[-1][name] = value
            if temp["capture"] != constants.nil:
                frame[-1]["_capture"] = temp["capture"]
            err = execute(temp["body"], frame)
            if err and err != error.STOP_FUNCTION:
                if err > 0: error.error(pos, file, f"Error in function {ins!r}")
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
                                error.error(pos, file, f"Function '{function.__name__}' expected a block!")
                                return (error.RUNTIME_ERROR, error.SYNTAX_ERROR)
                            instruction_pointer, body = temp
                            t_args.append(body)
                        elif i.endswith("_body"):
                            temp = get_block(code, instruction_pointer)
                            if temp is None:
                                error.error(pos, file, f"Function '{function.__name__}' expected a block!")
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
                        error.error(pos, file, message)
                        return int(ecode)
            except:
                error.error(pos, file, traceback.format_exc()[:-1])
                return error.PYTHON_ERROR
        elif ins == "local" and argc == 1:
            execute(args[0]["body"], frame)
        elif ins == "on_new_scope" and argc == 0:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                error.error(pos, file, f"on_new_scope expected a block!")
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
                "from":f"dpl:{file}:{pos}"
            })
        elif ins == "on_pop_scope" and argc == 0:
            temp = get_block(code, instruction_pointer)
            if temp is None:
                error.error(pos, file, f"on_new_scope expected a block!")
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
                "from":f"dpl:{file}:{pos}"
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
            error.error(pos, file, f"Invalid instruction {ins}")
            return error.RUNTIME_ERROR
        instruction_pointer += 1
    else:
        return 0
    error.error(pos, file, "Error was raised!")
    return error.SYNTAX_ERROR

class IsolatedParser:
    def __init__(self, file_name="__main__", main_path=".", libdir=info.PERM_LIBDIR, argv=None):
        self.defaults = {
            "libdir":info.PERM_LIBDIR,
            "argv":info.ARGV.copy(),
            "main_file":varproc.internal_attributes["main_file"],
            "main_path":varproc.internal_attributes["main_path"],
            "meta":copy(varproc.meta_attributes),
        }
        varproc.internal_attributes["main_file"] = file_name
        varproc.internal_attributes["main_path"] = main_path
        info.LIBDIR = libdir
    def __enter__(self):
        return self
    def run(self, code, frame=None):
        if isinstance(code, str):
            code = process(code)
        return run(code, frame=frame)
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
def run(code, frame=None):
    """
    Run code generated by 'process'
    The code below only needs to run
    at depth=1 so we dont need to run these
    every scope that needs to run.
    More performance! Yum ;)
    """
    instruction_pointer = 0
    if isinstance(code, int):
        return code
    if isinstance(code, dict):
        is_llir = code["llir"]
        code, nframe = code["code"], code["frame"]
    else:
        is_llir = False
        nframe = new_frame()
    if frame is not None:
        frame[0].update(nframe[0])
    else:
        frame = nframe
    
    # the process function returned
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
    return execute(code, frame)

def get_run():
    return run

##################################
#      BEWARE DARK SOURCERY      #
##################################
# this is classified as dark magic...

# Doesnt use module.name = value
# so that when we change the names
# we dont need to go scour every file.

# to avoid circular imports
# basically instead of an "import"
# is equivalent to "export to"
mod_s.register_run(execute)
mod_s.register_process(process)
argproc_setter.set_run(execute)
