// src/c_lib/text_stats_engine.h

#ifndef TEXT_STATS_ENGINE_H
#define TEXT_STATS_ENGINE_H

#include <string>
#include <cstdlib>

// Standard cross-platform macro for exporting functions from a DLL/SO
#ifdef _WIN32
    #define DLL_EXPORT __declspec(dllexport)
#else
    // For Linux/macOS, use 'visibility' attribute for explicit export
    #define DLL_EXPORT __attribute__((visibility("default")))
#endif

// Functions exposed for the Python wrapper
extern "C" {
    /**
     * @brief Calculates the word count of the text.
     * * Words are counted by splitting the text using various whitespace separators, 
     * mirroring the behavior of Python's str.split().
     *
     * @param text The input string (expected to be UTF-8 encoded).
     * @return The calculated number of words.
     */
    DLL_EXPORT int calculate_word_count_c(const char* text);

    /**
     * @brief Calculates the character count of the text.
     *
     * @param text The input string (expected to be UTF-8 encoded).
     * @param include_spaces 1 (True) to include all whitespace characters, 
     * 0 (False) to exclude all whitespace.
     * @return The calculated number of characters/bytes.
     */
    DLL_EXPORT int calculate_character_count_c(const char* text, int include_spaces);

    /**
     * @brief Calculates the read time of the given text.
     *
     * @param word_count The word count of the text.
     * @param wpm The words per minute (Read Time)
     * @return The calculated read time in String Format.
     */
    DLL_EXPORT const char* calculate_read_time_c(int word_count, int wpm);
}

#endif // TEXT_STATS_ENGINE_H