import atexit
from . import varproc
from . import info
from .arguments import *
from .varproc import *
from . import error
from .objects import *
from . import constants
from .type_checker import *
from . import error
from . import extension_support as ext_s
import time
from . import utils

def my_exit_atexit(code=0):
    if info.unique_imports:
        print(f"\nPerformed {len(info.imported):,} non-identical imports\nPerformed {info.unique_imports:,} total imports")

atexit.register(my_exit_atexit)

# setup runtime stuff. And yes on import.
# user will have to manually define type signatures
# or lower the type checker strictness by setting TC_DEFAULT_WHEN_NOT_FOUND
try:
    import psutil

    CUR_PROCESS = psutil.Process()

    def get_memory(_, __):
        memory_usage = CUR_PROCESS.memory_info().rss
        return (utils.convert_bytes(memory_usage),)

    varproc.meta_attributes["internal"]["HasGetMemory"] = 1
    varproc.meta_attributes["internal"]["GetMemory"] = get_memory
except ModuleNotFoundError as e:
    varproc.meta_attributes["internal"]["HasGetMemory"] = 0
    varproc.meta_attributes["internal"]["GetMemory"] = lambda _, __: error.get_error_string("PYTHON_ERROR", "GetMemory is unavailable.")

varproc.meta_attributes["internal"]["SetEnv"] = os.putenv,
varproc.meta_attributes["internal"]["GetEnv"] = os.getenv

varproc.meta_attributes["internal"]["os"] = {
    "uname": info.SYS_MACH_INFO,  # uname
    "architecture": info.SYS_ARCH,  # system architecture (commonly x86 or ARMv7 or whatever arm proc)
    "executable_format": info.EXE_FORM,  # name is self explanatory
    "machine": info.SYS_MACH,  # machine information
    "information": info.SYS_INFO,  # basically the tripple
    "processor": info.SYS_PROC,  # processor (intel and such)
    "threads": os.cpu_count(),  # physical thread count,
    "os_name":info.SYS_OS_NAME.lower(),
}

if info.UNIX and info.SYS_OS_NAME == "linux":
    varproc.meta_attributes["internal"]["os"]["linux"] = {
        "name": info.LINUX_DISTRO,
        "version": info.LINUX_VERSION,
        "codename": info.LINUX_CODENAME
}

if "get-internals" in info.program_flags:
    varproc.meta_attributes["argument_processing"] = {
        "process_argument":process_arg,
        "process_argumemts":process_args,
        "preprocess_arguments":exprs_preruntime,
        "evaluate":evaluate
    }
    
    varproc.meta_attributes["variable_processing"] = {
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
    varproc.meta_attributes["internal"]["SizeOf"] = get_size_of
except:

    def temp(_, __, ___):
        return f"err:{error.PYTHON_ERROR}:Cannot get memory usage of an object!\nIf you are using pypy, pypy does not support this feature."

    varproc.meta_attributes["internal"]["SizeOf"] = temp