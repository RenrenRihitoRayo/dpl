# /lib/std-c/_build_.py
# Build C libraries for DPL
# Maybe in the future this will
# become a command instead.

import glob
from os.path import abspath
from os import system, name, remove

# Add more here
compilers = {
    "gcc": "-shared -fPIE -o {file_out} {file_in}",
    "clang": "-shared -fPIE -o {file_out} {file_in}",
}

ext = ".dll" if name == "nt" else ".so"

print("= Looking for compilers")
for cc in compilers:
    if system(f"{cc} --version"):
        continue
    print(f"= Found {cc}")
    break
else:
    print("= No suitable compilers found.")
    exit(1)

print("= Compiling libraries...")
err = 0
for file_in in glob.glob("./lib/*.c"):
    file_in = abspath(file_in)
    name = abspath(file_in).rsplit('.', 1)[0]
    print(f"    Compiling {file_in} ...")
    if system(cc + " " + compilers[cc].format(
        file_in = file_in,
        file_out = name + ext
    )):
        print("    ^ Failed!")
    else:
        print(f"    ^ Compiled to {name + ext}")

print("= Cleanup")
for name in glob.glob("*.so")+glob.glob("*.dll"):
    print(f"    Deleting {name} ...")
    try:
        remove(name)
    except:
        print(f"    ^ Failed!")

print("= Done!")
if err:
    print(f"= {err} Error" + ("s" if err > 1 else ""))