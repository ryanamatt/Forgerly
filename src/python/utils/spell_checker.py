# src/python/utils/spell_checker.py

from .ffi_base import ffi, lib
from pathlib import Path

ffi.cdef("""
    typedef void* SpellCheckerHandle;
    
    typedef struct {
        char word[256];
        int distance;
    } SuggestionOutput;
    
    SpellCheckerHandle spell_checker_create();
         
    void spell_checker_destroy(SpellCheckerHandle handle);
         
    void spell_checker_load_dictionary(SpellCheckerHandle handle, const char** words, int count);
         
    void spell_checker_load_custom(SpellCheckerHandle handle, const char** words, int count);
         
    void spell_checker_add_custom(SpellCheckerHandle handle, const char* word);
         
    void spell_checker_remove_custom(SpellCheckerHandle handle, const char* word);
         
    int spell_checker_is_correct(SpellCheckerHandle handle, const char* word);
         
    int spell_checker_get_suggestions(SpellCheckerHandle handle, const char* word, int max_distance,
        SuggestionOutput* output_array, int* output_count);
""")

class SpellChecker:
    """
    Python wrapper for the C++ SpellCheckerEngine.
    Manages lifecycle and provides Pythonic interface.
    """
    def __init__(self) -> None:
        """
        Initialize the spell checker engine.
        
        :rtype: None
        """
        self._handle = lib.spell_checker_create()
        if not self._handle:
            raise RuntimeError("Failed to create SpellCheckerEngine instance.")
        
    def __del__(self) -> None:
        """
        "Cleanup when garbage collected.
        
        :rtype: None
        """
        if self._handle:
            lib.spell_checker_destroy(self._handle)
            self._handle = None

    
    def load_dictionary(self, words: list[str]) -> None:
        """
        Bulk load dictionary words into the spell checker.
        
        :param words: List of dictionary words (will be normalized to lowercase)
        :type words: list[str]
        :rtype: None
        """
        if not words:
            return
        
        c_word_list = [ffi.new("char[]", w.encode('utf-8')) for w in words]
        c_words = ffi.new("char* []", c_word_list)

        lib.spell_checker_load_dictionary(self._handle, c_words, len(words))

    def load_custom_words(self, words: list[str]) -> None:
        """
        Bulk load custom words (character names, lore terms, etc.).
        
        :param words: A list of words.
        :type words: list[str]
        :rtype: None
        """
        if not words:
            return
        
        # Convert Python strings to C array
        c_words = ffi.new("char*[]", len(words))
        for i, word in enumerate(words):
            c_words[i] = ffi.new("char[]", word.encode('utf-8'))
        
        lib.spell_checker_load_custom(self._handle, c_words, len(words))

    def add_custom_word(self, word: str) -> None:
        """
        Add a single custom word (e.g., new character name).
        
        :param: word: The word to add
        :type word; str
        :rtype: None
        """
        if word:
            lib.spell_checker_add_custom(self._handle, word.encode('utf-8'))
    
    def remove_custom_word(self, word: str) -> None:
        """
        Remove a custom word.
        
        :param: word: The word to remove
        :type word; str
        :rtype: None
        """
        if word:
            lib.spell_checker_remove_custom(self._handle, word.encode('utf-8'))
    
    def is_correct(self, word: str) -> bool:
        """
        Check if a word is spelled correctly.
        
        :param word: The word to check
        :type word: str  
        :returns: True if word is in dictionary or custom words, False otherwise
        :rtype: bool
        """
        if not word:
            return False
        
        result = lib.spell_checker_is_correct(self._handle, word.encode('utf-8'))
        return bool(result)
    
    def get_suggestions(self, word: str, max_distance: int = 2, max_results: int = 10) -> list[dict]:
        """
        Get spelling suggestions for a misspelled word.
        
        :param word: The word to get suggestions for
        :type word: str
        :param max_distance: Maximum edit distance (default 2)
        :type max_distance: int
        :param max_results: Maximum number of suggestions to return (default 10)
        :type max_results: int
        returns: List of dicts with 'word' and 'distance' keys, sorted by distance
        :rtype: list[dict]
        """
        if not word:
            return []
        
        # Allocate output array (up to 100 suggestions internally)
        output_array = ffi.new("SuggestionOutput[100]")
        output_count = ffi.new("int*", 0)
        
        result = lib.spell_checker_get_suggestions(
            self._handle,
            word.encode('utf-8'),
            max_distance,
            output_array,
            output_count
        )
        
        if result != 0:
            return []
        
        # Convert C results to Python list
        suggestions = []
        count = min(output_count[0], max_results)
        for i in range(count):
            suggestions.append({
                'word': ffi.string(output_array[i].word).decode('utf-8'),
                'distance': output_array[i].distance
            })
        
        return suggestions
    
    def load_dictionary_from_file(self, filepath: str) -> int:
        """
        Convenience method to load dictionary from a text file.
        
        :param filepath: Path to dictionary file (one word per line)
        :type filepath: str
        :returns: Number of words loaded
        :rtype: int
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Dictionary file not found: {filepath}")
        
        words = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().lower()
                if word and word.isalpha():  # Only alphabetic words
                    words.append(word)
        
        self.load_dictionary(words)
        return len(words)


# Singleton instance for global access
_global_spell_checker = None

def get_spell_checker() -> SpellChecker:
    """
    Get the global spell checker instance (creates if needed).
    
    :returns: The SpellChecker.
    :rtype: SpellChecker
    """
    global _global_spell_checker
    if _global_spell_checker is None:
        _global_spell_checker = SpellChecker()
    return _global_spell_checker

if __name__ == "__main__":
    checker = get_spell_checker()
    checker.load_dictionary(["apple", "banana"])

    print(checker.is_correct("apple"))   # Should be True
    print(checker.is_correct("orange"))  # Should be False