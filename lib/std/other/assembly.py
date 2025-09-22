import mmap
import ctypes
from keystone import Ks, KS_ARCH_X86, KS_MODE_64, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN

ks = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)
code, _ = ks.asm("mov x0, #42; ret")

def run_native(code_bytes):
    buf = mmap.mmap(-1, len(code_bytes), prot=mmap.PROT_WRITE|mmap.PROT_READ|mmap.PROT_EXEC)
    buf.write(bytes(code_bytes))
    func_type = ctypes.CFUNCTYPE(ctypes.c_uint64)
    func = func_type(ctypes.addressof(ctypes.c_void_p.from_buffer(buf)))
    return func

# makes python exit at -1
print(run_native(code)())
