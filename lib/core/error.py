# Logging

import datetime
import enum
import os
import sys
import random

log_stack = []
error_stack = []

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
    "LIBRARY_NOT_FOUND",
    "SYNTAX_ERROR",
    "RUNTIME_ERROR",
    "PYTHON_ERROR",
    "IMPORT_ERROR",
    "TYPE_ERROR",
    "NAME_ERROR",
    "COMPAT_ERROR",
    "FILE_NOT_FOUND_ERROR",
    "REFERENCE_ERROR",
    "CHECK_ERROR",
    "ASSERTION_ERROR"
)

happy_assertion_success = [
    "Hey, not broken. Nice.",
    "I’d say that worked... barely.",
    "Well, look at you, actually doing it right.",
    "Code survived my scrutiny. Congrats.",
    "Hmm, didn't expect that to pass. Good job.",
    "You didn't mess this one up. Miracles happen.",
    "Okay, that's actually solid.",
    "Not too shabby, keep it up.",
    "Your code isn't trash this time.",
    "Finally, a green light. Enjoy it.",
    "Surprisingly competent work, mate.",
    "Look at you, obeying the laws of logic.",
    "Not broken, so I'll shut up for now.",
    "You might know what you’re doing after all.",
    "This is one less headache for me. Thanks.",
    "Well, that was painless.",
    "Nice, didn’t even need my intervention.",
    "Your code passes. Weird flex.",
    "Good enough to ship... maybe.",
    "Huh, actually correct. Shocked myself reading this."
]

happy_assertion_failure = [
    "Well... that exploded. Try again.",
    "Oops, logic called in sick today.",
    "Congrats, you found a bug.",
    "That assertion is crying. Fix it.",
    "Your code hates you right now.",
    "Close, but no cigar. Debug time.",
    "Yikes. That didn't work.",
    "Better luck next iteration.",
    "Well, that failed spectacularly.",
    "Not even close. Keep digging.",
    "I believe in you... sort of.",
    "Debug, rinse, repeat.",
    "You're learning, right? Prove it.",
    "The interpreter laughed at you. Harsh.",
    "Well, this is awkward. Fix it.",
    "Try harder, the code won't debug itself.",
    "Error 404: Success not found.",
    "Back to the drawing board, friend.",
    "Your code says 'nope' today.",
    "Assertion failed. I'm judging you silently."
]

META_ERR = None
PREPROCESSING_FLAGS = None

def error_setup_meta(scope):
    global META_ERR, PREPROCESSING_FLAGS

    META_ERR = scope
    PREPROCESSING_FLAGS = scope["preprocessing_flags"]
    scope["err"].update({
        "builtins": ERRORS,
        "defined_errors": list(ERRORS),
        "log_stack": log_stack,
        "error_stack": error_stack
    })
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


def error(pos, file, cause=None):
    if file == "__main__":
        file = META_ERR["internal"]["main_file"]
    og_print(f"\nError in line {pos} file {file!r}", file=sys.stderr)
    if cause is not None:
        og_print(f"Cause:\n{cause}", file=sys.stderr)
    sys.stderr.flush()
    log_stack.append(err:={
        "line": pos,
        "file": file,
        "message": cause,
        "level": 3
    })
    error_stack.append(err)

def info_extra(pos, file, cause=None):
    if file == "__main__":
        file = META_ERR["internal"]["main_file"]
    og_print(f"\n[INFO] {datetime.datetime.now()}\nLine {pos} in file {file!r}", file=sys.stderr)
    if cause is not None:
        og_print(f"Details: {cause.replace(chr(10), chr(10)+'         ')}", file=sys.stderr)
    sys.stderr.flush()
    log_stack.append(err:={
        "line": pos,
        "file": file,
        "message": cause,
        "level": 1
    })
    error_stack.append(err)

def info_assert_true(pos, file, expression):
    cause = f"{expression} was true!\n{random.choice(happy_assertion_success)}"
    if file == "__main__":
        file = META_ERR["internal"]["main_file"]
    og_print(f"\n[INFO] {datetime.datetime.now()}\nLine {pos} in file {file!r}", file=sys.stderr)
    if cause is not None:
        og_print(f"Details: {cause.replace(chr(10), chr(10)+'         ')}", file=sys.stderr)
    sys.stderr.flush()
    log_stack.append(err:={
        "line": pos,
        "file": file,
        "message": cause,
        "level": 1
    })
    error_stack.append(err)

def info_assert_false(pos, file, expression):
    cause = f"{expression} was false!\n{random.choice(happy_assertion_failure)}"
    if file == "__main__":
        file = META_ERR["internal"]["main_file"]
    og_print(f"\n[INFO] {datetime.datetime.now()}\nLine {pos} in file {file!r}", file=sys.stderr)
    if cause is not None:
        og_print(f"Details: {cause.replace(chr(10), chr(10)+'         ')}", file=sys.stderr)
    sys.stderr.flush()
    log_stack.append(err:={
        "line": pos,
        "file": file,
        "message": cause,
        "level": 3
    })
    error_stack.append(err)

og_print = my_print
is_silent = []

def info(text, show_date=True):
    if show_date:
        og_print(f"[INFO] {datetime.datetime.now()}: {text}")
    else:
        og_print(f"[INFO]: {text}")
    sys.stdout.flush()
    log_stack.append({
        "line": "??",
        "file": "??",
        "message": text,
        "level": 1
    })

def warning(pos, file, text):
    if file == "__main__":
        file = META_ERR["internal"]["main_file"]
    og_print(f"\nWarning for line {pos} file {file!r}\n[WARNING]: {text}")
    sys.stdout.flush()
    log_stack.append({
        "line": "??",
        "file": "??",
        "message": text,
        "level": 2
    })


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
