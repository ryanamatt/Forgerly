import os
import sys
from cffi import FFI

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

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

_bundled_lib_path = get_resource_path(os.path.join('src', 'c_lib', _LIB_NAME))

try:
    # Try the bundled path first
    if os.path.exists(_bundled_lib_path):
        lib = ffi.dlopen(_bundled_lib_path)
    else:
        # Fallback for development mode
        _lib_path_local = os.path.join(os.path.dirname(__file__), '..', '..', 'c_lib', _LIB_NAME)
        lib = ffi.dlopen(_lib_path_local)
except Exception as e:
    # Final attempt: let the OS search system paths
    try:
        lib = ffi.dlopen(_LIB_NAME)
    except Exception:
        raise ImportError(f"CRITICAL: Failed to load C++ core library: {e}")