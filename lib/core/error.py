# Logging

import datetime
import os

class DPLError(Exception):
    def __init__(self, code):
        self._code = code
        self._name = ERRORS_DICT.get(code, '???')
        super().__init__()
    @property
    def name(self): return self._name
    @property
    def code(self): return self._code
    def __repr__(self):
        return f"DPLError(code={self._code!r}, name={self._name!r})"
    def __str__(self):
        return self.__repr__()

ERRORS = (
    "PREPROCESSING_ERROR",
    "SYNTAX_ERROR",
    "RUNTIME_ERROR",
    "PYTHON_ERROR",
    "PANIC_ERROR",
    "IMPORT_ERROR",
    "THREAD_ERROR",
    "TYPE_ERROR",
    "NAME_ERROR",
    "COMPAT_ERROR",
    "FILE_NOT_FOUND_ERROR"
)

META_ERR = None
PREPROCESSING_FLAGS = None

def error_setup_meta(scope):
    global META_ERR, PREPROCESSING_FLAGS
    META_ERR = scope
    PREPROCESSING_FLAGS = scope["preprocessing_flags"]
    scope["err"].update({"builtins": ERRORS, "defined_errors": list(ERRORS)})
    
    for pos, name in enumerate(ERRORS, 1):
        globals()[name] = pos
        META_ERR[name] = pos
        META_ERR[pos] = name

def register_error(name, value=None):
    if name in META_ERR:
        return META_ERR[name]
    META_ERR["defined_errors"].append(name)
    META_ERR[name] = (
        err_id := len(META_ERR["defined_errors"]) if value is None else value
    )
    META_ERR[err_id] = name
    ERRORS_DICT[err_id] = name
    return err_id

STOP_RESULT = -1
SKIP_RESULT = -2
FALLTHROUGH = -3
STOP_FUNCTION = -4

ERRORS_DICT = {
    globals().get(name): name for name in filter(lambda x: x.endswith("ERROR"), dir())
}

def my_print(*args, **kwargs):
    if PREPROCESSING_FLAGS["RUNTIME_ERRORS"]:
        print(*args, **kwargs)

def get_error_string(name, message):
    return None if name not in ERRORS_DICT else f"err:{ERRORS_DICT.get(name)}:{message}"

def pre_error(pos, file, cause=None):
    og_print(f"\n[Preprocessing Error]\nError in line {pos} file {file!r}")
    if cause is not None:
        og_print(f"Cause:\n{cause}")


def error(pos, file, cause=None):
    og_print(f"\nError in line {pos} file {file!r}")
    if cause is not None:
        og_print(f"Cause:\n{cause}")


og_print = my_print  # Use this to always call an error even when silent
is_silent = []

def info(text, show_date=True):
    if show_date:
        og_print(f"   [INFO] {datetime.datetime.now()}: {text}")
    else:
        og_print(f"   [INFO]: {text}")


def warnf(pos, file, text):
    og_print(f"\nWarning for line {pos} file {file!r}\n[WARNING]: {text}")


def warn(text, show_date=True):
    if show_date:
        og_print(f"[WARNING] {datetime.datetime.now()}: {text}")
    else:
        og_print(f"[WARNING]: {text}")

def pre_info(text, show_date=True):
    if show_date:
        og_print(f"   [INFO PRE] {datetime.datetime.now()}: {text}")
    else:
        og_print(f"   [INFO PRE]: {text}")


def pre_warn(text, show_date=True):
    if show_date:
        og_print(f"[WARNING PRE] {datetime.datetime.now()}: {text}")
    else:
        og_print(f"[WARNING PRE]: {text}")

# make the errors toggleable
def silent():
    global print
    og_print = lambda *x, **y: ...
    is_silent.append(0)

def active():
    global print
    is_silent.pop()
    if not is_silent:
        og_print = my_print