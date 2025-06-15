import ast
import os
import sys
import importlib.util
import sysconfig

seen = set()
dependencies = set()
print(sys.stdlib_module_names)

def resolve_module_file(modname, by=None):
    try:
        spec = importlib.util.find_spec(modname)
        if spec and spec.origin and spec.origin.endswith(".py"):
            return os.path.abspath(spec.origin), by
        elif spec and spec.origin == "built-in":
            dependencies.add((modname, by))
            return None, None
        elif modname in sys.stdlib_module_names:
            dependencies.add((modname, by))
            return None, None
    except Exception:
        # namespacing problem maybe relative import
        # or runtime import
        return None, None
    # not found
    return None, None

def extract_imports_from_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        node = ast.parse(f.read(), filename=filepath)
    for stmt in ast.walk(node):
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                yield alias.name.split('.')[0], filepath
        elif isinstance(stmt, ast.ImportFrom):
            if stmt.module:
                yield stmt.module.split('.')[0], filepath

def walk_module(modname, set=False, by=None):
    if modname in seen:
        return
    
    if set:
        seen.add(modname)
    else:
        by = "module-" + modname

    file, by = resolve_module_file(modname, by)
    if not file:
        return  # probably built-in or extension

    dependencies.add((modname, by))

    for imported, by in extract_imports_from_file(file):
        walk_module(imported, True, by)

# --- Entry point ---
if __name__ == "__main__":
    entry = sys.argv[1] if len(sys.argv) > 1 else "dpl.py"

    # Prime the entry script manually
    entry_modname = os.path.splitext(os.path.basename(entry))[0]
    walk_module(entry_modname)

    print("Dependencies:")
    for dep, by in sorted(dependencies):
        print(by, "=>", dep)
