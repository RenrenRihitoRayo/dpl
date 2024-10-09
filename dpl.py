# DPL CLI
# We use match statements for the CLI
# To keep it lightweight, we dont need speed here.

import os
import lib.core.info as info
import lib.core.parser as parser
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
                varproc.meta["internal"]["search_paths"].insert(0, varproc.meta["internal"]["main_path"])
                parser.run(code)
        case ["repr"]:
            frame = varproc.new_frame()
            print("DPL REPL for DPL 0.1")
            while True:
                act = input(">>> ").strip()
                if act and act.split(maxsplit=1)[0] in info.INC:
                    while True:
                        aa = input("... ")
                        if not aa:
                            break
                        act += "\n"+aa
                elif act == "exit":
                    break
                parser.run(parser.process(act), frame=frame)
        case _:
            print("Invalid commands!")

if __name__ == "__main__":
    handle_args()