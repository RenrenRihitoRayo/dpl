import os

local = os.path.dirname(__file__)

if os.path.isfile(temp:=os.path.join(local, "py_parser.c")):
    os.remove(temp)

print(f"Building parser.{os}")

os.chdir(local)
os.system("python3.13 setup.py build_ext --inplace")
