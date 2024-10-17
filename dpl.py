# DPL CLI
# We use match statements for the CLI
# To keep it lightweight, we dont need speed here.

import os
import pickle
import lib.core.info as info
try: # Try to use the .pyd or .so parser to get some kick
    import lib.core.parser as parser
    print("   [INFO]: Using compiled parser!")
except Exception as e: # fallback to normal python impl if it fails
    import lib.core.py_parser as parser
import lib.core.varproc as varproc
import lib.core.utils as utils

def handle_args():
    match (info.ARGV[1:]):
        case ["run", file, *args]:
            if not os.path.isfile(file):
                print("Invalid file path:", file)
                exit(1)
            if os.path.isfile("meta_config.cfg"):
                with open("meta_config.cfg", "r") as f:
                    varproc.meta = utils.parse_config(f.read(), {"meta":varproc.meta})["meta"]
            info.ARGV.clear()
            info.ARGV.extend([file, *args])
            info.ARGC = len(info.ARGV)
            varproc.meta["argc"] = info.ARGC
            with open(file, "r") as f:
                code = parser.process(f.read())
                varproc.meta["internal"]["main_path"] = os.path.dirname(os.path.abspath(file))+os.sep
                if (err:=parser.run(code)):
                    print(f"\n[{file}]\nFinished with an error: {err}")
                parser.IS_STILL_RUNNING.set()
                if err:
                    exit(1)
        case ["rc", file, *args]:
            if not os.path.isfile(file):
                print("Invalid file path:", file)
                exit(1)
            if os.path.isfile("meta_config.cfg"):
                with open("meta_config.cfg", "r") as f:
                    varproc.meta = utils.parse_config(f.read(), {"meta":varproc.meta})["meta"]
            info.ARGV.clear()
            info.ARGV.extend([file, *args])
            info.ARGC = len(info.ARGV)
            varproc.meta["argc"] = info.ARGC
            try:
                with open(file, "rb") as f:
                    code = pickle.loads(f.read())
                    varproc.meta["internal"]["main_path"] = os.path.dirname(os.path.abspath(file))+os.sep
                    if (err:=parser.run(code)):
                        print(f"\n[{file}]\nFinished with an error: {err}")
                    parser.IS_STILL_RUNNING.set()
                    if err:
                        exit(1)
            except Exception as e:
                print("Something went wrong:", file)
                print("Error:", repr(e))
                exit(1)
        case ["compile", file]:
            if not os.path.isfile(file):
                print("Invalid file path:", file)
                exit(1)
            output = file.rsplit(".", 1)[0]+".cdpl"
            try:
                with open(file, "r") as in_file:
                    with open(output, "wb") as f:
                        f.write(pickle.dumps(parser.process(in_file.read())))
            except Exception as e:
                print("Something went wrong:", file)
                print("Error:", repr(e))
                exit(1)
        case ["repr"] | []:
            if os.path.isfile(os.path.join(info.BINDIR, 'start_prompt.txt')):
                start_text = open(os.path.join(info.BINDIR, 'start_prompt.txt')).read()
            else:
                start_text = ""
            frame = varproc.new_frame()
            PROMPT_CTL = frame[-1]["_meta"]["internal"]["prompt_ctl"] = {}
            PROMPT_CTL["ps1"] = ">>> "
            PROMPT_CTL["ps2"] = "..."
            print(f"DPL REPL for DPL {varproc.meta['internal']['version']}\nPython {info.PYTHON_VER}{(chr(10)+start_text) if start_text else ''}")
            START_FILE = os.path.join(info.BINDIR, "start_script.dpl")
            if os.path.isfile(START_FILE):
                try:
                    with open(START_FILE, "r") as f:
                        parser.run(parser.process(f.read(), name="dpl_repl-startup"))
                except:
                    print("something went wrong while running start up script!")
            while True:
                try:
                    act = input(PROMPT_CTL["ps1"]).strip()
                except KeyboardInterrupt:
                    exit()
                if act and act.split(maxsplit=1)[0] in info.INC or act == "#multiline":
                    while True:
                        try:
                            aa = input(PROMPT_CTL["ps2"])
                        except KeyboardInterrupt:
                            exit()
                        if not aa:
                            break
                        act += "\n"+aa
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
                                parser.run(parser.process(f.read(), name="dpl_repl-startup"))
                        except:
                            print("something went wrong while running start up script!")
                    continue
                try:
                    if (err:=parser.run(parser.process(act), frame=frame)):
                        print(f"Error Code: {err}")
                except Exception as e:
                    print(f"Python Exception was raised while running:\n{repr(e)}")
        case _:
            print("Invalid invokation!")
            exit(1)

if __name__ == "__main__":
    handle_args()