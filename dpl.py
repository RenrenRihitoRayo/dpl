#!/usr/bin/env python3

# DPL CLI
# We use match statements for the CLI
# To keep it lightweight, we dont need speed here.


import lib.core.info as info
import lib.core.cli_arguments as cli_args
info.program_flags = prog_flags = cli_args.flags(info.ARGV, True)
import time
import sys

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

sys.set_int_max_str_digits(2**30) 
sys.setrecursionlimit(2**30)

import lib.core.utils as utils
import lib.core.error as error
import os
if "skip-non-essential" not in prog_flags:
    import cProfile
    from dfpm import dfpm
    import prompt_toolkit
    InMemoryHistory = prompt_toolkit.history.InMemoryHistory
    prompt =  prompt_toolkit.prompt
    WordCompleter = prompt_toolkit.completion.WordCompleter
    import subprocess
    import shutil
    import lib.core.extension_support as ext_s
    import pstats
    import project_mngr.pmfdpl as pkg_manager
    ext_s.modules.prompt_toolkit = prompt_toolkit
    ext_s.modules.cProfile = cProfile
    ext_s.modules.pstats = pstats
    ext_s.shutil = shutil
    ext_s.subrocess = subprocess
    import lib.core.suggestions as suggest
    
if "use-python" not in prog_flags:
    try:  # Try to use the .pyd or .so parser to get some kick
        try:
            import lib.core.parser as parser
        except ImportError as e:
            raise ImportError(f"Non-Python Parser had an error while importing: {e}") from e
        except Exception as e:
            raise Exception(f"Non-Python Parser had difficulties: {e}")
        meta["internal"]["implementation"] = "non-python"
    except Exception as e:  # fallback to normal python impl if it fails
        if "show-parser-import" in prog_flags: print(e)
        import lib.core.py_parser as parser
else:
    import lib.core.py_parser as parser
import lib.core.varproc as varproc

import dill

help_str = f"""Help for DPL [v{varproc.meta['internal']['version']}]

Commands:
dpl run [file] args...
    Runs the given DPL script.
dpl rc [file] args...
    Runs the given compiled DPL script.
dpl compile [file]
    Compiles the given DPL script.
    Outputs to [file].cdpl
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
dpl -use-python
    Explicitly use the python based parser.
    This bypasses the imports to any parser.so or parser.pyi files.
dpl -show-parser-import
    Prints if any errors arised while importing the non-python based parser.
dpl -no-lupa
    Do not import lupa components.
dpl -no-cffi
    Do not import cffi components.
dpl -instant-help
    Prints the help string without using the command matching.
dpl -get-internals
    Insert interpreter internals in "_meta"
    Scopes that will be defined:
    - "argument_processing": Functions to process arguments.
    - "variable_processing": Functions to manipulate a frame.
"""

def rec(this, ind=0):
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


def ez_run(code, process=True, file="???"):
    "Run a DPL script in an easier way, hence ez_run"
    if process:
        code = parser.process(code)
    if err := parser.run(code):
        print(f"\n[{file}]\nFinished with an error: {err}")
        rec(err)
    parser.IS_STILL_RUNNING.set()
    parser.clean_threads()
    if err:
        if isinstance(err, tuple):
            exit(err[0])
        else:
            exit(err)

if "instant-help" in prog_flags:
    print(help_str)
    exit(0)

if "simple-run" in prog_flags:
    if "init-time" in prog_flags:
        END = time.perf_counter() - INIT_START_TIME
        s, u = utils.convert_sec(END)
        print(f"DEBUG: Initialization time: {s}{u}")
    with open(sys.argv[0], "r") as f:
        ez_run(f.read())
    exit(0)

def handle_args():
    if "version" in varproc.flags or "v" in varproc.flags:
        print(
            f"DPL v{info.VERSION}\nUsing Python {info.PYTHON_VER}\n© Darren Chase Papa 2024\nMIT License (see LICENSE)"
        )
        return
    match (info.ARGV):
        case ["run", file, *args]:
            if not os.path.isfile(file):
                print("Invalid file path:", file)
                exit(1)
            info.ARGV.clear()
            varproc.meta["argc"] = info.ARGC = len(info.ARGV)
            with open(file, "r") as f:
                varproc.meta["internal"]["main_path"] = (
                    os.path.dirname(os.path.abspath(file)) + os.sep
                )
                varproc.meta["internal"]["main_file"] = file
                ez_run(
                    f.read(),
                    file=file
                )
        case ["rc", file, *args]:
            if not os.path.isfile(file):
                print("Invalid file path:", file)
                exit(1)
            info.ARGV.clear()
            varproc.meta["argc"] = info.ARGC = len(info.ARGV)
            try:
                with open(file, "rb") as f:
                    code = dill.loads(f.read())
                    varproc.meta["internal"]["main_file"] = file
                    varproc.meta["internal"]["main_path"] = (
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
            if not os.path.isfile(file):
                print("Invalid file path:", file)
                exit(1)
            output = file.rsplit(".", 1)[0] + ".cdpl"
            try:
                with open(file, "r") as in_file:
                    with open(output, "wb") as f:
                        f.write(dill.dumps(parser.process(in_file.read())))
            except Exception as e:
                print("Something went wrong:", file)
                print("Error:", repr(e))
                exit(1)
        case ["pm", *args]:
            sys.exit(handle_cmd(args))
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
            frame = varproc.new_frame()
            cmd_hist = InMemoryHistory()
            acc = []
            if not "-disable-auto-complete" in prog_flags:
                import lib.core.repl_syntax_highlighter as repl_conf
                for f in frame:
                    acc.extend(utils.flatten_dict(f).keys())
                    acc.extend(map(lambda x:":"+x, utils.flatten_dict(f).keys()))
                    acc.extend(map(lambda x:"%"+x, utils.flatten_dict(f).keys()))
            PROMPT_CTL = frame[-1]["_meta"]["repl_conf"] = {}
            PROMPT_CTL["ps1"] = ">>> "
            PROMPT_CTL["ps2"] = "... "
            START_FILE = os.path.join(info.BINDIR, "repl_conf/startup.dpl")
            if os.path.isfile(START_FILE):
                try:
                    with open(START_FILE, "r") as f:
                        parser.run(parser.process(f.read()), frame)
                except:
                    print("something went wrong while running start up script!")
            while True:
                try:
                    act = prompt(PROMPT_CTL["ps1"], completer=WordCompleter(acc+suggest.SUGGEST, pattern=suggest.pattern), history=cmd_hist, lexer=repl_conf.DPLLexer(), style=repl_conf.style).strip()
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
                            aa = prompt(PROMPT_CTL["ps2"], completer=WordCompleter(acc+suggest.SUGGEST, pattern=suggest.pattern), history=cmd_hist).strip()
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
                            with open(START_FILE, "r") as f:
                                parser.run(
                                    parser.process(f.read(), name="dpl_repl-startup")
                                )
                        except:
                            print("something went wrong while running start up script!")
                    continue
                try:
                    if err := parser.run(parser.process(act, "./repr.dpl-instance"), frame=frame):
                        rec(err)
                    if not "-disable-auto-complete" in prog_flags:
                        acc = []
                        for f in frame:
                            acc.extend(utils.flatten_dict(f).keys())
                            acc.extend(map(lambda x:":"+x, utils.flatten_dict(f).keys()))
                except Exception as e:
                    print(f"Python Exception was raised while running:\n{repr(e)}")
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
