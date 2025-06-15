ext = dpl.extension(meta_name="compiler")
# supported targets
ext.items["targets"] = ["python"]
# compilation result
ext.items["result"] = []
# curent indent
ext.items["indent"] = 0
# curent target (default python)
ext.items["target"] = "python"

compile_error = dpl.error.register_error("COMPILE_ERROR")

def indent(code):
    return (ext.items["indent"]*"  ")+code.replace("\n", "\n"+(ext.items["indent"]*"  "))

def process_arg(arg):
    if ext.items["target"] == "python":
        return str(arg)
    else:
        raise Exception(f"Unsupported target {ext.items['target']}")

def process_args(args):
    return ", ".join(map(process_arg, args))

@ext.add_func()
def compile_body(_, __, main_body):
    for [pos, file, ins, args] in main_body:
        match [ins, *args]:
            case ["print", *args]:
                if ext.items["target"] == "python":
                    ext.items["result"].append(indent(f"print({process_args(args)})"))
            case ["set", var, "=", value]:
                if ext.items["target"] == "python":
                    ext.items["result"].append(indent(f"{var} = {process_arg(value)}"))
            case _:
                return f"err:{compile_error}:Couldnt compile {ins!r}"

@ext.add_func()
def collect(frame, _, name):
    frame[-1][name] = "\n".join(ext.items["result"])
    ext.items["result"].clear()