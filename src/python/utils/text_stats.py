# src/python/utils/text_stats.py

from .ffi_base import ffi, lib

# Append text-specific definitions
ffi.cdef("""
    int calculate_word_count(const char* text);
    int calculate_character_count(const char* text, int include_spaces);
    const char* calculate_read_time(int word_count, int wpm);
""")

def calculate_word_count(text: str) -> int:
    text_bytes = text.encode('utf-8')
    return lib.calculate_word_count(text_bytes)

def calculate_character_count(text: str, include_spaces: bool = True) -> int:
    text_bytes = text.encode('utf-8')
    c_include_spaces = 1 if include_spaces else 0
    return lib.calculate_character_count(text_bytes, c_include_spaces)

def calculate_read_time(word_count: int, wpm: int = 250) -> str:
    result_ptr = lib.calculate_read_time(word_count, wpm)
    if result_ptr:
        return ffi.string(result_ptr).decode('utf-8')
    return "0 min"