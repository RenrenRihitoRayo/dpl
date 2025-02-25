import os


def run(python_bin):
    print(f"Building with {python_bin}")
    local = os.path.dirname(__file__)
    if os.path.isfile(temp := os.path.join(local, "py_parser.c")):
        os.remove(temp)

    print(f"Building parser.{os}")

    os.chdir(local)
    os.system(f"{python_bin} setup.py build_ext --inplace")
