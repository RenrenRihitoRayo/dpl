import os, sys

up = 0

def process(code, file="__main__"):
    global up
    res = []
    for pos, line in enumerate(code.split("\n"), 1):
        up += 1
        line = line.lstrip()
        if line.startswith("#") or not line:
            continue
        elif line.startswith("@"):
            line = line[1:].lstrip()
            if " " in line:
                ins, arg = line.split(maxsplit=1)
            else:
                ins, arg = line, None
            if ins == "extend" and arg is not None:
                with open(arg, "r") as f:
                    res.extend(process(f.read(), file=arg))
            else:
                print(f"Error: Invalid directive {ins!r}\nLine {pos}\nFile {file}")
        else:
            if " " in line:
                ins, arg = line.split(maxsplit=1)
            else:
                ins, arg = line, None
            if ins == "!label":
                print("Defined:", arg, pos, up-1)
                VARS[arg] = up-1
            else:
                res.append((pos, file, ins, arg))
    return res

def expr(text):
    ntext = text.strip()
    if ntext.startswith('"') and ntext.endswith('"'):
        return ntext[1:-1]
    elif ntext.endswith("n"):
        try:
            return int(ntext[:-1])
        except:
            try:
                return float(ntext[:-1])
            except:
                return text
    elif ntext.startswith("."):
        return ntext[1:]
    elif ntext.startswith("[") and ntext.endswith("]"):
        return eval(ntext[1:-1], {"__builtins__":{}, **VARS})
    else:
        return res if (res:=VARS.get(text, text)) is not None else ""

VARS = {}
stack = []

def run(code):
    if isinstance(code, str):
        code = process(code)
    else:
        ...
    p = 0
    name = None
    ret = []
    flag = 0
    while p < len(code):
        pos, file, ins, arg = code[p]
        print("::", pos, p, ins); input()
        if arg is not None:
            arg = expr(arg)
        else:
            arg = ""
        if ins == "push" and arg is not None:
            stack.append(arg)
        elif ins == "println" and stack: print(stack.pop())
        elif ins == "dump":
            print("Variables:")
            for n, v in VARS.items():
                print(f"{n} = {v}")
            print("\nStack:")
            if not stack:
                print("[empty]")
            for p, v in filter(lambda x: x[1], enumerate(stack)):
                print(f"{p:08} : {v}")
            print("\nReturn Stack:")
            print(ret or "[empty]")
        elif ins == "print" and stack: print(stack.pop(), end="")
        elif ins == "def" and arg is not None: name = arg
        elif ins == "set" and arg is not None and name is not None: VARS[name] = arg; name = None
        elif ins == "label" and arg is not None: VARS[arg] = str(p)
        elif ins == "goto" and arg is not None: p = VARS.get(arg, p+1); continue
        elif ins == "eq" and name is not None and arg is not None:
            if name == arg: flag = 1
            else:           flag = 0
            name = None
        elif ins == "ne" and name is not None and arg is not None:
            if name != arg: flag = 1
            else:            flag = 0
            name = None
        elif ins == "gt" and name is not None and arg is not None:
            if name > arg: flag = 1
            else:          flag = 0
            name = None
        elif ins == "lt" and name is not None and arg is not None:
            if name < arg: flag = 1
            else:          flag = 0
        elif ins == "jinz" and arg is not None:
            if flag:
                p = VARS.get(arg, p+1)-1
                continue
        elif ins == "jize" and arg is not None:
            if not flag:
                p = VARS.get(arg, p+1)-1
                continue
        elif ins == "gsinz" and arg is not None:
            if flag:
                ret.append(p)
                p = VARS.get(arg, p+1)-1
                continue
        elif ins == "gsize" and arg is not None:
            if not flag:
                ret.append(p)
                p = VARS.get(arg, p+1)-1
                continue
        elif ins == "gosub" and arg is not None:
            ret.append(p)
            print("Jump to", arg)
            p = VARS.get(arg, p+1)-1
            continue
        elif ins == "return":
            if ret:
                p = ret.pop()
            else:
                print(f"\nError: Return stack underflow!\nLine {pos}\nFile {file}")
                break
        elif ins == "cmd" and arg is not None:
            res = os.system(arg)
            if name is not None:
                VARS[name] = str(res)
        elif ins == "halt":
            print("\nDone!"); return 0
        else:
            print(f"\nInvalid Instruction: {ins}\n{ret}\nLine {pos}\nFile {file}")
            break
        p += 1
    return 0

def main():
    try:
        with open(sys.argv[1], "r") as f:
            run(f.read())
    except Exception as e:
        print(repr(e))

if __name__ == "__main__":
    sys.argv.append("test.txt")
    main()
