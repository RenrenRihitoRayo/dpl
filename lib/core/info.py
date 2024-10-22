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

DEC = {
    "end"
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
else:
    BINDIR = "~/.dpl"
    LIBDIR = os.path.join(BINDIR, "lib")
    CORE_DIR = os.path.join(LIBDIR, "core")

PYTHON_VER = sys.version

SYS_ARCH, EXE_FORM = platform.architecture()
SYS_PROC = platform.processor()
SYS_MACH = platform.machine()
SYS_INFO = platform.platform()
SYS_MACH_INFO = platform.uname()

if __name__ == "__main__":
    for name, value in globals().copy().items():
        print(f"{name} = {value!r}")