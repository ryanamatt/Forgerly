# src/python/utils/text_stats_wrapper.py

# Ensure Compilation of C++ Library
# g++ -shared     -o src/c_lib/text_stats_engine_lib.dll     src/c_lib/text_stats_engine.cpp     -Isrc/c_lib -std=c++17     -Wl,--out-implib,src/c_lib/libtext_stats_engine.a     -static-libstdc++ -static-libgcc -static


import ctypes
import os
import sys

# --- Configuration ---
# Define the C library name based on the target OS
if sys.platform.startswith('win'):
    _LIB_NAME = "text_stats_engine_lib.dll"
elif sys.platform.startswith('linux'):
    _LIB_NAME = "text_stats_engine_lib.so"
elif sys.platform.startswith('darwin'):
    _LIB_NAME = "text_stats_engine_lib.dylib"
else:
    _LIB_NAME = "text_stats_engine_lib.so" 

_stats_engine = None

try:
    # 1. Attempt to load the library from a relative path
    _lib_path_local = os.path.join(os.path.dirname(__file__), '..', '..', 'c_lib', _LIB_NAME)
    
    # Try loading from the local path first, then try the system path
    try:
        # Load the compiled C++ Dynamic Library
        _stats_engine = ctypes.CDLL(_lib_path_local)
    except FileNotFoundError:
        _stats_engine = ctypes.CDLL(_LIB_NAME)

    # 2. Define C Function Signatures using ctypes

    # int calculate_word_count_c(const char* text);
    _stats_engine.calculate_word_count_c.argtypes = [ctypes.c_char_p]
    _stats_engine.calculate_word_count_c.restype = ctypes.c_int

    # int calculate_character_count_c(const char* text, int include_spaces);
    _stats_engine.calculate_character_count_c.argtypes = [ctypes.c_char_p, ctypes.c_int]
    _stats_engine.calculate_character_count_c.restype = ctypes.c_int
    
    # const char* calculate_read_time_c(int word_count, int wpm); 
    _stats_engine.calculate_read_time_c.argtypes = [ctypes.c_int, ctypes.c_int]
    _stats_engine.calculate_read_time_c.restype = ctypes.c_char_p # Correct: C string pointer

    # void free_string_c(const char* ptr); 
    # NEW: Function to manage memory allocated by the C++ side
    _stats_engine.free_string_c.argtypes = [ctypes.c_char_p]
    _stats_engine.free_string_c.restype = None
    
except Exception as e:
    # We raise an ImportError to make it explicit that the dependency
    # on the C++ library could not be met.
    error_msg = f"CRITICAL: Failed to load C++ statistical engine ({_LIB_NAME}). Application cannot proceed without it. Error: {e}"
    raise ImportError(error_msg)


# --- Public Wrapper Functions (Only call C++ engine) ---

def calculate_word_count(text: str) -> int:
    """Calculates the word count using the C++ engine."""
    # Encode Python string to bytes (UTF-8) for C's const char*
    text_bytes = text.encode('utf-8')
    return _stats_engine.calculate_word_count_c(text_bytes)

def calculate_character_count(text: str, include_spaces: bool = True) -> int:
    """Calculates the character count using the C++ engine."""
    text_bytes = text.encode('utf-8')
    # Cast boolean to C integer (1 or 0)
    c_include_spaces = 1 if include_spaces else 0
    return _stats_engine.calculate_character_count_c(text_bytes, c_include_spaces)

def calculate_read_time(word_count: int, wpm: int = 250) -> str:
    """Calculates the estimated read time using the C++ engine."""
    # Call the C++ function, which returns a const char* pointer
    result_ptr = _stats_engine.calculate_read_time_c(word_count, wpm)

    if result_ptr:
        # Decode the C char* result back to a Python string
        result_str = result_ptr.decode('utf-8')

        return result_str

    return "0 min"