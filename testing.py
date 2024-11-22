import dpl
import sys
import os

temp_out = []

test_dir = "tests"

import builtins as b

files = map(lambda x: os.path.join(test_dir, x), os.listdir(test_dir))

def get_head(file):
    setup = []
    snaps = []
    output = []
    temp = []
    name = "???"
    with open(file, "r") as f:
        for i in f.read().split("\n"):
            i = i.strip()
            if i == "#end":
                snaps.append((name, "\n".join(output) if output else None, "\n".join(setup+temp)))
                output.clear(); temp.clear(); name = None
            elif i.startswith("#output:"):
                output.append(i[8:])
            elif i.startswith("#name:"):
                name = i[6:].strip()
            elif i.startswith("#:"):
                setup.append(i[2:])
            else:
                temp.append(i)
    return snaps

def test(name, code, exp_output=None):
    oldp = b.print
    def print(*args, sep=" ", end="\n", file=sys.stdout):
        temp = sep.join(map(str, args))+end
        file.write(temp)
        file.flush()
        temp_out.append(temp)
    b.print = print
    dpl.ez_run(code)
    output = "".join(temp_out)
    temp_out.clear()
    b.print = oldp

    if output != exp_output:
        print("\n"+(f"[ Test {name!r} failed! ]".center(50, "-")))
        print(f"-- Code --\n{code}\n-- Output --\n{output}")
    else:
        print("\n"+(f" Passed: {name}".rjust(40, "-")))

def test_all():
    for file in files:
        snaps = get_head(file)
        for name, exp, code in snaps:
            test(name, code, exp)

if __name__ == '__main__':
    test_all()
    input()