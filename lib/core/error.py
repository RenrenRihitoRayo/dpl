# Logging

import datetime
import enum
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
    "IMPORT_ERROR",
    "TYPE_ERROR",
    "NAME_ERROR",
    "COMPAT_ERROR",
    "FILE_NOT_FOUND_ERROR",
    "REFERENCE_ERROR"
)

META_ERR = None
PREPROCESSING_FLAGS = None

def error_setup_meta(scope):
    global META_ERR, PREPROCESSING_FLAGS

    META_ERR = scope
    PREPROCESSING_FLAGS = scope["preprocessing_flags"]
    scope["err"].update({"builtins": ERRORS, "defined_errors": list(ERRORS)})
    PREPROCESSING_FLAGS = scope["preprocessing_flags"]
    for pos, name in enumerate(ERRORS, 1):
        globals()[name] = pos
        scope["err"][name] = pos
        scope["err"][pos] = name

def register_error(name, value=None):
    if name in META_ERR:
        return META_ERR[name]
    META_ERR["err"]["defined_errors"].append(name)
    META_ERR["err"][name] = (
        err_id := len(META_ERR["err"]["defined_errors"]) if value is None else value
    )
    META_ERR["err"][err_id] = name
    ERRORS_DICT[err_id] = name
    return err_id

CONTROL_CODES = (
    "STOP_RESULT",
    "SKIP_RESULT",
    "FALLTHROUGH",
    "STOP_FUNCTION"
)

globals().update({name:-index for index, name in enumerate(CONTROL_CODES, 1)})

CONTROL_DICT = {-index: name for index, name in enumerate(CONTROL_CODES, 1)}

ERRORS_DICT = {name: index for name, index in enumerate(ERRORS, 1)}

def my_print(*args, **kwargs):
    if PREPROCESSING_FLAGS["RUNTIME_ERRORS"]:
        print(*args, **kwargs)

def get_error_string(name, message):
    return None if name not in ERRORS_DICT else f"err:{ERRORS_DICT.get(name)}:{message}"

def pre_error(pos, file, cause=None):
    if file == "__main__":
        file = META_ERR["internal"]["main_file"]
    og_print(f"\n[Preprocessing Error]\nError in line {pos} file {file!r}")
    if cause is not None:
        og_print(f"Cause:\n{cause}")


def error(pos, file, cause=None):
    if file == "__main__":
        file = META_ERR["internal"]["main_file"]
    og_print(f"\nError in line {pos} file {file!r}")
    if cause is not None:
        og_print(f"Cause:\n{cause}")


og_print = my_print
is_silent = []

def info(text, show_date=True):
    if show_date:
        og_print(f"   [INFO] {datetime.datetime.now()}: {text}")
    else:
        og_print(f"   [INFO]: {text}")


def warning(pos, file, text):
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
    global og_print
    og_print = lambda *x, **y: ...
    is_silent.append(1)

def active():
    global og_print
    is_silent.pop()
    if not is_silent:
        og_print = my_print