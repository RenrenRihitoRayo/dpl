#!/usr/bin/env python3

# DPL CLI
# We use match statements for the CLI
# To keep it lightweight, we dont need speed here.


# what in the import hell is this?
import sys
_file_ = sys.argv[0]
import lib.core.info as info
info.original_argv = sys.argv.copy()
import lib.core.cli_arguments as cli_args
prog_flags, prog_vflags = cli_args.flags(info.ARGV, remove_first=True)
import lib.core.module_handling as mod_s
mod_s.modules.cli_arguments = cli_args
mod_s.modules.sys = sys
info.program_flags = prog_flags
info.program_vflags = prog_vflags
info.ARGC = len(info.ARGV)
import time
import traceback

# Simple mode
if "simple-mode" in prog_flags:
    prog_flags.update((
        "skip-non-essential",
        "no-lupa",
        "no-cffi",
        "disable-auto-complete"
    ))

# Debug mode
if "debug-mode" in prog_flags:
    prog_flags.update((
        "init-time",
    ))

info.imported = set()
info.unique_imports = 0
og_import = __import__
def __my_import__(module, globals=None, locals=None, from_list=tuple(), level=0):
    name = module or "???"
    if "show-imports-as-is" in prog_flags:
        print(":: import", name, flush=True)
    else:
        if name not in info.imported:
            print(":: import", name, flush=True)
            info.imported.add(name)
    info.unique_imports += 1
    return og_import(module, globals, locals, from_list, level)
if "show-imports" in prog_flags or "show-imports-as-is" in prog_flags:
    print("DEBUG: __import__ bypass has been set.\nExpect debug output for every import.")
    __builtins__.__import__ = __my_import__

if "init-time" in prog_flags:
    INIT_START_TIME = time.perf_counter()

import lib.core.utils as utils
import lib.core.error as error
import os
mod_s.modules.os = os
# Python is slow. This is evidence.
if "skip-non-essential" not in prog_flags:
    import cProfile
    from dfpm import dfpm
    import prompt_toolkit
    InMemoryHistory = prompt_toolkit.history.InMemoryHistory
    prompt =  prompt_toolkit.prompt
    WordCompleter = prompt_toolkit.completion.WordCompleter
    import subprocess
    import shutil
    import pstats
    mod_s.modules.prompt_toolkit = prompt_toolkit
    mod_s.modules.cProfile = cProfile
    mod_s.modules.pstats = pstats
    mod_s.modules.shutil = shutil
    mod_s.modules.subrocess = subprocess
    import pprint
    import lib.core.serialize_dpl as cereal # i was hungry
    from lib.core.py_parser2_internals.py_parser2_internals import op_code_registry
    import lib.core.ast_gen as ast_gen
    import misc.dpl_linter as linter
    import lib.core.suggestions as suggest
else:
    prompt = lambda text=None, *x, **y: input(text)
    WordCompleter = InMemoryHistory = lambda *x, **y: ...
    suggest = type("suggest:simple", (object,), {
        "SUGGEST": [],
        "pattern": ""
    })

# removed try except here.
if "use-parser2" in prog_flags:
    import lib.core.py_parser2 as parser
    has_pp2 = True
    if "ignore-expiramental" not in prog_flags: print("!!! WARNING: USING NEW EXPIRAMENTAL PARSER !!!\n")
else:
    import lib.core.py_parser as parser
    has_pp2 = False

import lib.core.varproc as varproc

help_str = f"""Help for DPL [v{varproc.meta_attributes['internal']['version']}]

Commands:
dpl run [file] args...
    Runs the given DPL script.
dpl compile [file]
    Compiles the given DPL script.
    Outputs to [file].cdpl
dpl rc [file] args...
    Runs the given compiled DPL script.
`dpl repl` ALSO JUST `dpl`
    Invokes the REPL
dpl package install <user> <repo> <branch> <include_branch_name?>
    Install a package hosted on github.
    Default branch is 'master'
dpl package installto: <path_to_dest> <user> <repo> <branch> <include_branch_name?>
    Install a package hosted on github.
    Default branch is 'master'
dpl package remove <package_name>
    Delete that package.
dpl get-docs file
    Get the doc comments.
dpl dump-hlir <file>
    Dumps the high level IR that DPL generates.
    Output is `[file].hlir`
dpl dump-llir <file>
    Dumps the low level IR that DPL generates.
    Output is `[file].llir`
    Must provide the "-use-py-parser2"
    to use.
dpl dump-ast <file.dpl>
    Dumps the ast of the given file.
    Outputs to `<file.dpl>.dplad`
dpl dump-ast-cdpl <file.cdpl>
    Dumps the ast of the given file.
    Outputs to `<file.cdpl>.dplad`

Note AST Dumps are not for execution
and only for program analysis.

Flags and such:
dpl -info
    Prints info.
dpl -arg-test
    Tests flag handling.
'dpl -version' or 'dpl -v'
    Prints version and some info.
'dpl -profile' or 'dpl -p'
    Profiles the code using 'time.perf_counter' for inaccurate but fast execution.
dpl -cprofile ...
    Profiles the code using cProfile for more accurate but slower execution.
dpl -disable-auto-complete
    Disable the auto complete.
dpl -init-time
    Show initialization time.
dpl -show-imports
    Show all imports done by dpl.
    Note thay this captures the imports also done by the imported modules.
dpl -simple-run
    Skip any cli handling and just take the first argument it sees and treats it as a file.
    Usage: dpl -simple-run file
    As the name suggests it doesnt handle any other argunents.
    This will also disble profiling.
dpl -skip-non-essential
    This skips any non essential imports that arent used when running files.
    This will mess up the REPL if misused.
dpl -show-parser-import
    Prints if any errors arised while importing the non-python based parser.
dpl -no-lupa
    Do not import lupa components.
dpl -instant-help
    Prints the help string without using the command matching.
dpl -get-internals
    Insert interpreter internals in "_meta"
    Variables that will be injected:
    - "argument_processing": Functions to process arguments.
    - "variable_processing": Functions to manipulate a frame.
dpl -use-py-parser2
    Use the new expiramental parser (INCOMPLETE)
    You also need to include the "&enable:EXPIRAMENTAL_LLIR"
    directive to use it.
dpl -ignore-expiramental
    Avoid printing warnings for expiramental
    options.
"""

def rec(this, ind=0):
    "Print errors [rec]ursively."
    if not isinstance(this, (tuple, list)):
        print(
            f"{'  '*ind}Error Name: {error.ERRORS_DICT.get(this, f'ERROR NAME NOT FOUND <{this}>')}"
        )
    else:
        for pos, i in enumerate(this):
            if isinstance(i, (tuple, list)):
                print(f"{'  '*ind}Cause:")
                rec(i, ind + 1)
            else:
                print(
                    f"{'  '*ind}Error Name {'(root) ' if pos == 0 else '(cause)'}: {error.ERRORS_DICT.get(i, f'ERROR NAME NOT FOUND <{i}>')}"
                )


def ez_run(code, file="???", process=True):
    "Run a DPL script in an easier way, hence ez_run"
    if process:
        code = parser.process_code(code)
    if err := parser.run_code(code):
        print(f"\n[{file}]\nFinished with an error: {err}")
        rec(err)
    if err:
        if isinstance(err, tuple):
            exit(err[0])
        else:
            exit(err)

def get_start_path(start):
    if os.path.isfile(start):
        return start
    elif os.path.isdir(start):
        if os.path.isfile(start_file:=os.path.join(start, "dpl_start.txt")):
            return os.path.join(start, open(start_file, "r").read().strip())
        elif os.path.isfile(start_file:=os.path.join(start, "main.dpl")):
            return start_file
        else:
            print(f"{start}: No valid start paths found!\ndpl_start.txt nor main.dpl was found in the directory.")
            exit(1)
    print(f"{start}: Path is invalid!")
    exit(1)

if "instant-help" in prog_flags:
    print(help_str)
    exit(0)

# if you just need to run a simple script.
# no cli just the script, no bloat.
if "simple-run" in prog_flags:
    if "init-time" in prog_flags:
        END = time.perf_counter() - INIT_START_TIME
        s, u = utils.convert_sec(END)
        print(f"DEBUG: Initialization time: {s}{u}")
    with open(get_start_path(sys.argv[0]), "r") as f:
        varproc.meta_attributes["argc"] = info.ARGC = len(info.ARGV)
        ez_run(f.read(), sys.argv[0])
    exit(0)

def handle_args():
    if "version" in varproc.flags or "v" in varproc.flags:
        print(
            f"DPL v{info.VERSION}\nUsing Python {info.PYTHON_VER}\n© Darren Chase Papa 2024\nMIT License (see LICENSE)"
        )
        return
    match (info.ARGV):
        case ["run", file, *args]:
            file = get_start_path(file)
            info.ARGV.clear()
            info.ARGV.extend([file, *args])
            varproc.meta_attributes["argc"] = info.ARGC = len(info.ARGV)
            with open(file, "r") as f:
                varproc.meta_attributes["internal"]["main_path"] = (
                    os.path.dirname(os.path.abspath(file)) + os.sep
                )
                varproc.meta_attributes["internal"]["main_file"] = file
                ez_run(
                    f.read(),
                    file=file
                )
        case ["dump-llir", file]:
            if not has_pp2:
                print("Suply the '-use-py-parser2' flag first!")
                exit(1)
            file = get_start_path(file)
            with open(os.path.basename(file)+".llir", "w") as output:
                varproc.meta_attributes["internal"]["main_path"] = (
                    os.path.dirname(os.path.abspath(file)) + os.sep
                )
                varproc.meta_attributes["internal"]["main_file"] = file
                info.ARGV.pop(0)
                varproc.meta_attributes["argc"] = info.ARGC = len(info.ARGV)
                with open(file) as inputf:
                    output.write("""Auto generated by dump-llir
If you meant to compile a dpl script use compile instead of dump-llir
since this is not parsable and is just the output of pprint.pprint.
This uses opcodes instead of strings to reduce the overhead in hashing.
In the future the dictionary may be replaced with
an array making it even faster and efficient.\n
If you are thinking this isnt readable like HLIR.
Well HLIR is the user-facing bytecode.
LLIR is implementation specific and may vary across versions
and is volatile, LLIR is used internally and not externally
unlike HLIR.\n
Code format: (
    line position,
    source file,
    instruction as opcode,
    arguments to the op function
)\n
Pipe line:
    old:
    source -> unprocessed lines ->
    preprocessing and optimizations ->
    hlir generation -> execution ->
    program output
    
    new:
    source -> unprocessed lines ->
    preprocessing and optimizations ->
    hlir generation -> llir transformation
    new dictionary dispatch parser ->
    program output\n\nOpcodes:\n""")
                    for index, func in enumerate(op_code_registry):
                        output.write(f"    {index:04} => {func.__name__}\n")
                    output.write("\n\n")
                    print("Processing and HLIR Generation...")
                    out = parser.process_code(inputf.read())
                    print("LLIR Transformation...")
                    parser.process_hlir(out)
                    output.write(pprint.pformat(out))
                    print("Done!")
        case ["dump-hlir", file]:
            file = get_start_path(file)
            with open(os.path.basename(file)+".hlir", "w") as output:
                varproc.meta_attributes["internal"]["main_path"] = (
                    os.path.dirname(os.path.abspath(file)) + os.sep
                )
                varproc.meta_attributes["internal"]["main_file"] = file
                info.ARGV.pop(0)
                varproc.meta_attributes["argc"] = info.ARGC = len(info.ARGV)
                with open(file) as inputf:
                    output.write("""Auto generated by dump-hlir
This is the high level ir for DPL, why high level?
As you can see you can almost reconstruct the source from this.
If you meant to compile a dpl script use compile instead of dump-hlir
since this is not parsable and is just the output of pprint.pprint.\n
Code format: (
    line position,
    source file,
    instruction,
    arguments)\n\n""")
                    print("Processing and HLIR Generation...")
                    output.write(pprint.pformat(parser.process_code(inputf.read())))
                    print("Done!")
        case ["dump-ast", file]:
            file = get_start_path(file)
            with open(f"{file}.dplad", "w") as output:
                with open(file) as input:
                    ast_gen.walk(ast_gen.gen_ast_from_str(input.read()), file=output)
        case ["dump-ast-cdpl", file]:
            file = get_start_path(file)
            with open(f"{file}.dplad", "w") as output:
                ast_gen.walk(ast_gen.gen_ast_from_cdpl(file), file=output)
        case ["rc", file, *args]:
            file = get_start_path(file)
            info.ARGV.clear()
            info.ARGV.extend([file, *args])
            varproc.meta_attributes["argc"] = info.ARGC = len(info.ARGV)
            try:
                with open(file, "rb") as f:
                    code = cereal.deserialize(f.read())
                    varproc.meta_attributes["internal"]["main_file"] = file
                    varproc.meta_attributes["internal"]["main_path"] = (
                        os.path.dirname(os.path.abspath(file)) + os.sep
                    )
                    ez_run(
                        code,
                        False,
                        file
                    )
            except Exception as e:
                print("Something went wrong:", file)
                print("Error:", repr(e))
                exit(1)
        case ["compile", file]:
            file = get_start_path(file)
            output = file.rsplit(".", 1)[0] + ".cdpl"
            try:
                with open(file, "r") as in_file:
                    with open(output, "wb") as f:
                        f.write(cereal.serialize(parser.process_code(in_file.read())))
            except Exception as e:
                print("Something went wrong:", file)
                print("Error:", repr(e))
                exit(1)
        case ["pm", *args]:
            import project_mngr.pmfdpl as pkg_manager
            pkg_manager.mfile = _file_
            sys.exit(pkg_manager.handle_cmd(args))
        case ["package", *args]:
            match args:
                case ["install", user, repo]:
                    dfpm.dl_repo(user, repo, location=info.LIBDIR)
                case ["install", user, repo, branch]:
                    dfpm.dl_repo(user, repo, branch, location=info.LIBDIR)
                case ["installto:", ipath, user, repo]:
                    dfpm.dl_repo(user, repo, location=ipath)
                case ["installto:", ipath, user, repo, branch]:
                    dfpm.dl_repo(user, repo, branch, location=ipath)
                case ["install", user, repo, branch, use]:
                    dfpm.dl_repo(
                        user,
                        repo,
                        branch,
                        location=info.LIBDIR,
                        use_branch_name=use == "true",
                    )
                case ["installto:", ipath, user, repo, branch, use]:
                    dfpm.dl_repo(
                        user,
                        repo,
                        branch,
                        location=ipath,
                        use_branch_name=use == "true",
                    )
                case ["remove", pack_name]:
                    if not os.path.isdir(
                        pack_path := os.path.join(info.LIBDIR, pack_name)
                    ):
                        print("Package doesnt exist!")
                        return
                    print(pack_path, "Is going to be removed.")
                    if input("Enter y to continue: ").lower() in {"y", "yes"}:
                        dfpm.delete(pack_path)
                    print("Done!")
                case _:
                    print("Invalid command!")
                    return
        case ["get-docs", file]:
            if not os.path.isfile(file):
                print("Invalid file path:", file)
                exit(1)
            res = []
            get = False
            with open(file) as file:
                for line_pos, oline in enumerate(file, 1):
                    line = oline.strip()
                    if get:
                        if line == "--":
                            get = False
                        else:
                            if not oline:
                                res.append("")
                            elif not oline.startswith('  '):
                                print(f"{file.name} [line {line_pos}]: Expected a 2-space indent!")
                                exit(1)
                            else:
                                res.append(oline.rstrip()[2:])
                        continue
                    if line == "--doc":
                        get = True
                    elif line.startswith("#:"):
                        res.append(line[2:])
            print("\n".join(res))
        case ["repl"] | []:
            error.error_setup_meta(varproc.meta_attributes)
            frame = varproc.new_frame()
            cmd_hist = InMemoryHistory()
            acc = []
            PROMPT_CTL = frame[-1]["_meta"]["repl_conf"] = {}
            PROMPT_CTL["ps1"] = ">>> "
            PROMPT_CTL["ps2"] = "... "
            START_FILE = os.path.join(info.BINDIR, "repl_conf/startup.dpl")
            if os.path.isfile(START_FILE):
                try:
                    with parser.IsolatedParser(file_name="start_up_script") as pip:
                        with open(START_FILE, "r") as f:
                            pip.run_code(f.read(), frame)
                except Exception as e:
                    print("something went wrong while running start up script!\n:", e)
                    with open("repl_startup_error.txt", "w") as err_f:
                        err_f.write(traceback.format_exc())
            if not "disable-auto-complete" in prog_flags:
                import lib.core.repl_syntax_highlighter as repl_conf
                for f in frame:
                    acc.extend(utils.flatten_dict(f).keys())
                    acc.extend(map(lambda x:":"+x, utils.flatten_dict(f).keys()))
                inp = lambda text: prompt(text, completer=WordCompleter(acc+suggest.SUGGEST, pattern=suggest.pattern), history=cmd_hist, lexer=repl_conf.DPLLexer(), style=repl_conf.style).strip()
            else:
                inp = __builtins__.input
            while True:
                try:
                    act = inp(PROMPT_CTL["ps1"])
                except (KeyboardInterrupt, EOFError):
                    exit()
                if (
                    act
                    and (
                        (temp := act.split(maxsplit=1)[0]) in info.INC
                        or temp in info.INC_EXT
                    )
                    or act == "#multiline"
                ):
                    while True:
                        try:
                            aa = inp(PROMPT_CTL["ps2"])
                        except (KeyboardInterrupt, EOFError):
                            exit()
                        if not aa:
                            break
                        act += "\n" + aa
                elif act == ".paste":
                    act = ""
                    while True:
                        tmp = input()
                        if tmp == ".done": break
                        act += tmp + "\n"
                elif act == "exit":
                    break
                elif act.startswith("$"):
                    try:
                        err = os.system(act[1:])
                    except BaseException as e:
                        err = f"Error Raised: {repr(e)}"
                    finally:
                        print("\nDone!")
                    if err:
                        print(f"Error Code: {err}")
                    else:
                        print("Success")
                    continue
                elif act == ".reload":
                    if os.path.isfile(START_FILE):
                        try:
                            with parser.IsolatedParser(file_name="start_up_script") as pip:
                                with open(START_FILE, "r") as f:
                                    pip.run_code(f.read(), frame)
                        except:
                            print("something went wrong while running start up script!")
                    continue
                try:
                    if err := parser.run_code(parser.process_code(act, "./repr.dpl-instance"), frame=frame):
                        rec(err)
                    if not "disable-auto-complete" in prog_flags:
                        acc = []
                        for f in frame:
                            acc.extend(utils.flatten_dict(f).keys())
                            acc.extend(map(lambda x:":"+x, utils.flatten_dict(f).keys()))
                except Exception as e:
                    print(f"Python Exception was raised while running:\n{repr(e)}")
        case ["extract", file]:
            with open(file) as f:
                linter.set_main(os.path.realpath(file))
                program = linter.Program(parser.process_code(f.read()))
                program.update()
                print("Runtime Imports:")
                for v in program.runtime_imports:
                    if isinstance(v, linter.UseLuaNode):
                        print(f"[{v.source_file}:{v.line_pos}] use_luaj {v.module}")
                    else:
                        print(f"[{v.source_file}:{v.line_pos}] use {v.module}{'' if not v.alias else f' as {v.alias}'}")
                print("Variables:")
                for v in program.variables:
                    print(f"[{v.source_file}:{v.line_pos}] {v.variable_name!r} = {v.variable_value}")
                print("Functions:")
                for v in program.functions:
                    print(f"[{v.source_file}:{v.line_pos}] {v.function_name!r}({', '.join(v.function_parameters)})")
        case ["help"]:
            print(help_str)
        case _:
            print("Invalid invokation!")
            print("See 'dpl help' for more")
            exit(1)
    if "pause" in prog_flags:
        input("\n[Press Enter To Finish]")

if "init-time" in prog_flags:
    END = time.perf_counter() - INIT_START_TIME
    s, u = utils.convert_sec(END)
    print(f"DEBUG: Initialization time: {s}{u}")

if "show-imports" in prog_flags and "exit-when-done-importing" in prog_flags:
    exit(0)

if "dry-run" in prog_flags:
    exit(0)

if __name__ == "__main__":
    varproc.flags.update(prog_flags)
    info.ARGC = len(info.ARGV)
    if "cprofile" in prog_flags:
        profiler = cProfile.Profile()
        profiler.enable()
    handle_args()
    if "cprofile" in prog_flags:
        profiler.disable()
        default = "tottime"
        order_by = None
        for i in prog_flags:
            if i.startswith("order-profile="):
                order_by = i[14:]
        print("\nProfile Result")
        stats = pstats.Stats(profiler)
        stats.sort_stats(order_by or default).print_stats()
