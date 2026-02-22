import atexit
from .arguments import exprs_preruntime, process_arg, process_args, expr_runtime, argproc_setter, group, nest_args, Expression, to_static, evaluate, parse_match, parse_dict, ID, parse_list, is_static, parse_tuple, parse_string, tag_handlers, flatten_dict, unpack
from .varproc import rget, rset, rpop, meta_attributes, register_execute, new_frame, nscope, pscope, on_new_scope, on_pop_scope
from . import error
from .error import STOP_FUNCTION, STOP_RESULT, SKIP_RESULT
from .objects import function_type, object_type, make_function, make_method, make_object, register_run_fn
from . import constants
from . import error
from . import module_handling as mod_s
import time
import os
from . import utils
from .info import SYS_OS_NAME, SYS_ARCH, SYS_INFO, EXE_FORM, SYS_MACH_INFO, SYS_PROC, SYS_OS_NAME, unique_imports, SYS_MACH, UNIX, imported, LINUX_DISTRO, LINUX_VERSION, LINUX_CODENAME, program_flags, INC_TERMINAL

error.error_setup_meta(meta_attributes)

def my_exit_atexit(code=0):
    if unique_imports:
        print(f"\nPerformed {len(imported):,} non-identical reported imports\nPerformed {unique_imports:,} total reported imports")

atexit.register(my_exit_atexit)

# setup runtime stuff. And yes onimport.
# user will have to manually define type signatures
# or lower the type checker strictness by setting TC_DEFAULT_WHEN_NOT_FOUND
try:
    import psutil

    CUR_PROCESS = psutil.Process()

    def get_memory(_, __):
        memory_usage = CUR_PROCESS.memory_info().rss
        return (utils.convert_bytes(memory_usage),)

    meta_attributes["internal"]["HasGetMemory"] = 1
    meta_attributes["internal"]["GetMemory"] = get_memory
except ModuleNotFoundError as e:
    meta_attributes["internal"]["HasGetMemory"] = 0
    meta_attributes["internal"]["GetMemory"] = lambda _, __: error.get_error_string("PYTHON_ERROR", "GetMemory is unavailable.")

meta_attributes["internal"]["SetEnv"] = os.putenv,
meta_attributes["internal"]["GetEnv"] = os.getenv

meta_attributes["internal"]["os"] = {
    "uname": SYS_MACH_INFO,  # uname
    "architecture": SYS_ARCH,  # system architecture (commonly x86 or ARMv7 or whatever arm proc)
    "executable_format": EXE_FORM,  # name is self explanatory
    "machine": SYS_MACH,  # machine information
    "information": SYS_INFO,  # basically the tripple
    "processor": SYS_PROC,  # processor (intel and such)
    "threads": os.cpu_count(),  # physical thread count,
    "os_name":SYS_OS_NAME.lower(),
}

meta_attributes["internal"]["os_name_general"] = os.name
# Above can be
# nt - windows based
# posix - posix compliant systems
# jython - running on a jython environment

if UNIX and SYS_OS_NAME == "linux":
    meta_attributes["internal"]["os"]["linux"] = {
        "name": LINUX_DISTRO,
        "version": LINUX_VERSION,
        "codename": LINUX_CODENAME
}

if "get-internals" in program_flags:
    meta_attributes["argument_processing"] = {
        "process_argument":process_arg,
        "process_argumemts":process_args,
        "preprocess_arguments":exprs_preruntime,
        "evaluate":evaluate
    }
    
    meta_attributes["variable_processing"] = {
        "rset":rset,
        "rget":rget,
        "rpop":rpop,
        "new_frame":new_frame,
        "pop_scope":pscope,
        "new_scope":nscope
    }

def get_size_of(_, __, object):
    return (utils.convert_bytes(sys.getsizeof(object)),)


try:
    get_size_of(0, 0, 0)
    meta_attributes["internal"]["getsizeof"] = get_size_of
except:

    def temp(_, __, ___):
        return f"err:{error.PYTHON_ERROR}:Cannot get memory usage of an object!\nIf you are using pypy, pypy does not support this feature."

    meta_attributes["internal"]["SizeOf"] = temp
