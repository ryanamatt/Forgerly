# src/python/utils/ffi_base.py
import os
import sys
from cffi import FFI

# --- Configuration ---
if sys.platform.startswith('win'):
    _LIB_NAME = "nf_core_lib.dll"
elif sys.platform.startswith('linux'):
    _LIB_NAME = "nf_core_lib.so"
elif sys.platform.startswith('darwin'):
    _LIB_NAME = "nf_core_lib.dylib"
else:
    _LIB_NAME = "nf_core_lib.so" 

ffi = FFI()

# Define common data structures used by multiple modules
ffi.cdef("""
    typedef struct {
        double x;
        double y;
    } Point;
""")

try:
    _lib_path_local = os.path.join(os.path.dirname(__file__), '..', '..', 'c_lib', _LIB_NAME)
    try:
        lib = ffi.dlopen(_lib_path_local)
    except OSError:
        lib = ffi.dlopen(_LIB_NAME)
except Exception as e:
    raise ImportError(f"CRITICAL: Failed to load C++ core library: {e}")