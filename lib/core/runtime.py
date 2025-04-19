from . import extension_support as ext_s
from . import info
from cffi import FFI
import traceback
import threading
import sys
from . import varproc
import atexit
import os

ext_s.dpl.ffi = FFI()

IS_STILL_RUNNING = threading.Event()

threads = []
thread_events = [] # Thread events, so any threads can be killed manually or automatically

def clean_threads():  # kill all threads and wait for them to terminate
    for i in thread_events:
        i.set()
    for i in threads:
        i.join()

def my_exit(code=0):
    IS_STILL_RUNNING.set()
    clean_threads()
    og_exit(code)


def my_exit_atexit(code=0):
    if info.unique_imports:
        print(f"\nPerformed {len(info.imported):,} non-identical imports\nPerformed {info.unique_imports:,} total imports")

atexit.register(my_exit_atexit)

og_exit = sys.exit
ext_s.dpl.exit = my_exit
sys.exit = my_exit
exit = my_exit

# setup runtime stuff. And yes on import.
try:
    import psutil

    CUR_PROCESS = psutil.Process()

    def get_memory(_, __):
        memory_usage = CUR_PROCESS.memory_info().rss
        return (utils.convert_bytes(memory_usage),)

    varproc.meta["internal"]["HasGetMemory"] = 1
    varproc.meta["internal"]["GetMemory"] = get_memory
except ModuleNotFoundError as e:
    varproc.meta["internal"]["HasGetMemory"] = 0
    varproc.meta["internal"]["GetMemory"] = lambda _, __: (state.bstate("nil"),)

varproc.meta["internal"].update(
    {
        "SetEnv": lambda _, __, name, value: os.putenv(name, value),
        "GetEnv": lambda _, __, name, default=None: os.getenv(name, default),
    }
)

varproc.meta["internal"]["os"] = {
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
    varproc.meta["internal"]["os"]["linux"] = {
        "name": info.LINUX_DISTRO,
        "version": info.LINUX_VERSION,
        "codename": info.LINUX_CODENAME
}


varproc.meta["threading"] = {
    "runtime_event": IS_STILL_RUNNING,
    "is_still_running": lambda _, __: IS_STILL_RUNNING.is_set(),
}

varproc.meta["str_intern"] = lambda _, __, string: sys.intern(string)


def get_size_of(_, __, object):
    return (utils.convert_bytes(sys.getsizeof(object)),)


try:
    get_size_of(0, 0, 0)
    varproc.meta["internal"]["SizeOf"] = get_size_of
except:

    def temp(_, __, ___):
        return f"err:{error.PYTHON_ERROR}:Cannot get memory usage of an object!\nIf you are using pypy, pypy does not support this feature."

    varproc.meta["internal"]["SizeOf"] = temp

def expose(d):
    d.update(globals())