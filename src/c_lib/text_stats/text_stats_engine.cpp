// src/c_lib/text_stats_engine.cpp

#include "text_stats_engine.h"
#include <cstring>
#include <cctype>
#include <iostream>

// Helper function to check for sentence-ending punctuation
inline bool is_sentence_terminator(char c) {
    return (c == '.' || c == '!' || c == '?');
}

/**
 * @brief Calculates the word count.
 * * Uses a simple state machine (in_word) to count transitions from whitespace 
 * to non-whitespace characters, replicating Python's split() functionality.
 */
int calculate_word_count_c(const char * text) {
    if (!text) {
        return 0;
    }
    int word_count = 0;
    bool in_word = false;

    // Use a pointer to iterate through the string
    for (const char* p = text; *p != '\0'; p++) {
        if (isspace(static_cast<unsigned char>(*p))) {
            in_word = false;
        } else {
            if (!in_word) {
                word_count++;
                in_word = true;
            }
        }
    }
    return word_count;
} 

/**
 * @brief Calculates the character count.
 */
int calculate_character_count_c(const char* text, int include_spaces) {
    if (!text) {
        return 0;
    }

    if (include_spaces) {
        // Count all bytes (equivalent to Python's len(text) on the encoded string)
        return static_cast<int>(strlen(text));
    } else {
        // Count only non-whitespace bytes, mirroring len("".join(text.split()))
        int char_count = 0;
        for (const char* p = text; *p != '\0'; ++p) {
            if (!isspace(static_cast<unsigned char>(*p))) {
                char_count++;
            }
        }
        return char_count;
    }
}

/**
 * @brief Calculates the read time of a number of wrods.
 */
const char* calculate_read_time_c(int word_count, int wpm) {
    if (wpm <= 0 || word_count == 0) {
        // Use strdup to dynamically allocate "0 min" and return the pointer
        return strdup("0 min");
    }

    // Integer division equivalent of ceil(word_count / wpm)
    int minutes = (word_count + wpm - 1) / wpm;

    std::string result;
    if (minutes == 0) {
        result = "<1 min";
    } else {
        result = std::to_string(minutes) + " min";
    }

    // Allocate the string on the heap and return the pointer
    return strdup(result.c_str());
}