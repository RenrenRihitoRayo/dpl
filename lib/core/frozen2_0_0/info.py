# Used for system info and other data
# Variables are handled in varproc.py

# THIS FILE SHOULD NOT IMPORT DPL MODULES AS A CIRCULAR IMPORT WILL HAPPEN
# ALMOST EVERY FILE IN lib.core IMPORTS THIS

import os
import sys
import platform

unique_imports = set()
program_flags = set()
program_vflags = {}
original_argv = []

# used by module_handling to determine
# which files should use the second libdir
lib_for = []
SECOND_LIBDIR = None

try:
    from . import constants
except ImportError:

    class constants:
        nil = 0
        true = 1
        false = 0
        none = None


ARGV = sys.argv
ARGC = len(ARGV)

# only one increments
INC_EXT_BUILTIN = {
    "match",
    "case",
    "fn",
    "fn::static",
    "method",
    "for",
    "loop",
    "while",
    "if",
    "dict",
    "with",
    "default",
    "enum",
    "ifmain",
    "switch",
    "begin",
    "on_new_scope",
    "on_pop_scope",
    "list",
    "string",
    "fn::inline",
    "string::inline",
    "benchmark",
    "struct"
}

# user exposed for INC and INC_EXT
INC_EXT = INC_EXT_BUILTIN.copy()

INCREMENTS = INC_EXT

# methods where they depend on
# runtime but are unclear
# for example
# [oldformat "${...}"]
# since its a normal string
# and since oldformat is also just a string
# before runtime
# DPL might accidentally evaluate this
# to fold it, when the string
# says otherwise
RT_EXPR = {
    "oldformat",
    "call", # side effects
    ".unique"
}

def add_runtime_dependent_method(name):
    RT_EXPR.add(name)

EXPR = {
    "tuple", "?tuple",
    "dict", "?dict",
    "?int", "?float", "?string",
    "len", "range", "irange",
    "reverse",
    'nil?', 'none?', 'def?',
    "eval",
    "!", "..", "..+",
    "+", "-", "/", "*", "//", "%", "%%",
    "=>", "or", "and", "not", "call::static",
    "len", "typeof", "to_ascii", "from_ascii", "slice",
    
}

FUNCTIONS = {
    'cmd',
    'exit',
    'wait_for_threads',
    'exec', 'sexec',
    'dump_vars', 'dump_scope', 'fallthrough',
    "from", "as", "checks", "follows", "satisfies"
}

CONSTANTS = {
    'true', 'false', 'nil', 'none', '...'
}

KEYWORDS = {
    'skip',
    'stop',
    'in', 'as', 'not', 'and', 'or',
    'raise',
    'set', 'del',
    'struct', 'dict', 'list',
}

ALL_INTRINSICS = INC_EXT | EXPR | {"end"} | KEYWORDS

CHARS = {
    "\\\\": "\\[lit_slash]",
    "\\n": "\n",
    "\\t": "\t",
    "\\s": " ",
    "\\v": "\v",
    "\\f": "\f",
    "\\r": "\r",
    "\\a": "\a",
    "\\0": "\0",
    "\\e": "\x1B",
    "\\[lit_slash]": "\\"
}

OPEN_P = "[("
CLOSE_P = (")","]")

class flags:
    WARNINGS = True      # Specific to warnings.
    ERRORS = True        # Logs, Warnings and Such

VERSION_STRING = "2.0.0-setup"

class Version:
    def __init__(self, ver_str):
        self.build = ""
        if "-" in ver_str:
            ver_str, self.build = ver_str.rsplit("-", 1)
            self.build = "-" + self.build
        if not (ver := tuple(filter(str.isdigit, ver_str.split(".")))) or len(ver) > 3:
            raise Exception(f"Invalid version format: {ver_str}")
        ver = (*map(int, ver),)
        self.version_tuple = ver + (0,) * (3 - len(ver))
    def __gt__(self, other):
        return other > self.version_tuple[:len(other)]
    def __lt__(self, other):
        return other < self.version_tuple[:len(other)]
    def __ge__(self, other):
        return other >= self.version_tuple[:len(other)]
    def __le__(self, other):
        return other <= self.version_tuple[:len(other)]
    def __eq__(self, other):
        return other == self.version_tuple[:len(other)]
    def __ne__(self, other):
        return not other == self.ver
    def isLater(self, other):
        return other > self
    def isExact(self, other):
        return other == self
    def isEarlier(self, other):
        return other < self
    def __getitem__(self, index):
        return self.version_tuple[index]
    def __iter__(self):
        return self.version_tuple
    def __repr__(self):
        return "v"+".".join(map(str, self.version_tuple)) + self.build
    def as_id(self):
        return "v"+"_".join(map(str, self.version_tuple)) + self.build

VERSION = Version(VERSION_STRING)
VERSION_TRIPLE = VERSION.version_tuple

BINDIR = os.path.dirname(ARGV[0])
LIBDIR = os.path.join(BINDIR, "lib")
# a copy that shouldnt be changed.
# Used by IsolatedParser for the default libdir.
PERM_LIBDIR = LIBDIR
CORE_DIR = os.path.join(BINDIR, "lib", "core")

if os.name == "nt":
    UNIX = False
else:
    UNIX = True

PYTHON_VER = sys.version
PYTHON_RAW_VER = (temp := sys.version_info).major, temp.minor, temp.micro

SYS_ARCH, EXE_FORM = platform.architecture()
EXE_FORM = EXE_FORM or constants.none
SYS_PROC = platform.processor() or constants.none
SYS_MACH = platform.machine()
SYS_INFO = platform.platform()
SYS_MACH_INFO = platform.uname()
SYS_OS_NAME = SYS_MACH_INFO.system.lower()

if UNIX: # probably linux so use distro to fetch more info
    try:
        import distro
        LINUX_DISTRO = distro.name() or 0
        LINUX_VERSION = distro.version() or 0
        LINUX_CODENAME = distro.codename() or 0
    except:
        LINUX_DISTRO = 0
        LINUX_VERSION = 0
        LINUX_CODENAME = 0


def get_path_with_lib(path):
    return os.path.join(LIBDIR, path)


def get_path_with_cwd(path):
    return os.path.join(os.getcwd(), path)


def print_info():
    for name, value in globals().copy().items():
        if name in {"os", "sys", "print_info", "platform"} or not name.isupper():
            continue
        if not name.startswith("__") and not name.startswith("__"):
            print(f"{name} = {value!r}")


if __name__ == "__main__":
    print_info()
