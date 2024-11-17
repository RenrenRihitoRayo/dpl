# Used to system info and other data
# Variables are handled in varproc.py

import os, sys
import platform

ARGV = sys.argv
ARGC = len(ARGV)

INC = {
    "fn", "method",
    "for", "loop", "while",
    "if", "if-then",
    "thread",
    "ismain", "isntmain",
    "expect", "expect-then",
    "body"
}

INC = {
    "fn":1,
    "method":1,
    "for":1,
    "loop":1,
    "while":1,
    "if":1,
    "if-then":2,
    "thread":1,
    "body":1,
    "expect":1,
    "expect-then":2
}

DEC = {
    "end", "then"
}

CHARS = {
    "\\\\":"\\[escape]",
    "\\n":"\n",
    "\\t":"\t",
    "\\s":" ",
    "\\v":"\v",
    "\\f":"\f",
    "\\r":"\r",
    "\\a":"\a",
    "\\0":"\0",
    "\\[win_nl]":"\r\n",
    "\\[posix_nl]":"\n",
    "\\[null]":"\0",
    "\\[alert]":"\a",
    "\\[escape]":"\\",
}

if os.name == "nt":
    BINDIR = os.path.dirname(ARGV[0])
    LIBDIR = os.path.join(BINDIR, "lib")
    CORE_DIR = os.path.join(BINDIR, "lib", "core")
    UNIX = False
else:
    BINDIR = os.path.dirname(sys.argv[0])
    LIBDIR = os.path.join(BINDIR, "lib")
    CORE_DIR = os.path.join(LIBDIR, "core")
    # lesson learned. dont over complicate linux stuff.
    # BINDIR = os.path.expanduser("~/.dpl")
    # LIBDIR = os.path.join(BINDIR, "lib")
    # CORE_DIR = os.path.join(LIBDIR, "core")
    UNIX = True

PYTHON_VER = sys.version

SYS_ARCH, EXE_FORM = platform.architecture()
SYS_PROC = platform.processor()
SYS_MACH = platform.machine()
SYS_INFO = platform.platform()
SYS_MACH_INFO = platform.uname()

if __name__ == "__main__":
    for name, value in globals().copy().items():
        if not name.startswith("__") and not name.startswith("__"):
            print(f"{name} = {value!r}")