import dill

def rset(dct, full_name, value, sep="."):
    "Set a variable"
    if not isinstance(full_name, str):
        return
    if "." not in full_name:
            dct[full_name] = value
    path = [*enumerate(full_name.split(sep), 1)][::-1]
    last = len(path)
    node = dct
    while path:
        pos, name = path.pop()
        if (
            pos != last
            and name in node
            and isinstance(node[name], dict)
        ):
            node = node[name]
        elif pos == last:
            node[name] = value

cache = {}

def config(code, pack=False):
    "Helper to create bindings for DPL"
    data = {}
    for lpos, line in enumerate(code.split("\n"), 1):
        line = line.lstrip()
        if line.startswith("#") or not line:
            continue
        elif line.startswith("scope:"):
            rset(data, line[6:].strip(), {})
            continue
        elif line.startswith("::"):
            module_name = line[2:].strip()
            if "." not in module_name:
                rset(data, module_name, mod:=__import__(module_name))
                continue
            module, *path = module_name.split(".")
            try:
                module = __import__(module)
            except Exception as e:
                raise e from None
            while path:
                name = path.pop(0)
                if hasattr(module, name) and len(path) > 1:
                    module = getattr(module, name)
                elif hasattr(module, name):
                    rset(data, name, getattr(module, name))
                else:
                    print(f"Error [line {lpos}]: Invalid attribute {name} from object {module} which has {dir(module)}!")
                    return None
            continue
        var_name, module_name = line.split("<=")
        module_name = module_name.strip()
        var_name = var_name.strip()
        if "." not in module_name:
            rset(data, var_name, mod:=__import__(module_name))
            continue
        module, *path = module_name.split(".")
        try:
            module = __import__(module)
        except Exception as e:
            raise e from None
        while path:
            name = path.pop(0)
            if hasattr(module, name) and len(path) > 1:
                module = getattr(module, name)
            elif hasattr(module, name):
                rset(data, var_name, getattr(module, name))
            else:
                print(f"Error [line {lpos}]: Invalid attribute {name} from object {module} which has {dir(module)}!")
                return None
    return data if not pack else dill.dumps(data)
