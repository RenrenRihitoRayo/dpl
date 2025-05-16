from . import py_parser as parser
import os
import fnmatch
import ast
from collections import defaultdict

def convert_bytes(byte):
    "Convert bytes to appropriate units"
    if byte < 1e3:
        return byte, "B"
    elif byte < 1e6:
        return byte * 1e-3, "KB"
    elif byte < 1e9:
        return byte * 1e-6, "MB"
    elif byte < 1e12:
        return byte * 1e-9, "GB"
    elif byte < 1e15:
        return byte * 1e-12, "TB"
    else:
        return byte * 1e-15, "PB"

class FileWalker:
    def __init__(self):
        self.filetype_processors = {}
        self.deps = defaultdict(dict)

    def add_filetype(self, pattern, processor):
        self.filetype_processors[pattern] = processor

    def _match_processor(self, filename):
        for pattern, processor in self.filetype_processors.items():
            if fnmatch.fnmatch(filename, pattern):
                return processor
        return None

    def scan(self, root_path):
        for dirpath, _, filenames in os.walk(root_path):
            for filename in filenames:
                processor = self._match_processor(filename)
                if processor:
                    full_path = os.path.join(dirpath, filename)
                    try:
                        processor(self.deps, full_path)
                    except Exception as e:
                        print(f"[!] Failed to process {full_path}: {e}")

    def get_results(self):
        return dict(self.deps)

def py_processor(deps, path):
    with open(path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=path)
        except SyntaxError:
            return
    deps[path] = {
        "definitions":[],
        "file_size":os.path.getsize(path)
    }
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [arg.arg for arg in node.args.args]
            if node.args.vararg:
                args.append(f"*{node.args.vararg.arg}")
            if node.args.kwarg:
                args.append(f"**{node.args.kwarg.arg}")
            deps[path]["definitions"].append({
                "name": node.name,
                "args": args,
                "line": node.lineno,
                "doc": ast.get_docstring(node) or "[not found]"
            })

def py_processor(deps, path):
    with open(path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=path)
        except SyntaxError:
            return
    deps[path] = {
        "definitions":[],
        "file_size":os.path.getsize(path)
    }

if __name__ == "__main__":
    from pprint import pprint
    import sys
    if len(sys.argv) < 2:
        print("Usage: python script.py <directory>")
    else:
        walker = FileWalker()
        walker.add_filetype("*.py", py_processor)
        walker.scan(argv[1])
        for file, files in walker.get_results().items():
            print("File:", file)
            for file in files["definitions"]:
                print(f"""    Function: {file['name']}({', '.join(file['args'])})
        Doc-str:
        {file['doc'].replace("\n", "\n        ")}
        Line: {file['line']}""")
            uv, us = convert_bytes(files["file_size"])
            print(f"File size: {uv}{us}")