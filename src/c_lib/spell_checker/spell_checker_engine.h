// src/c_lib/spell_checker/spell_checker_engine.h

#ifndef SPELL_CHECKER_ENGINE_H
#define SPELL_CHECKER_ENGINE_H

#include <string>
#include <vector>

// Forward declaration
struct TrieNode;

struct SuggestionResult {
    std::string word;
    int distance;
};

class SpellCheckerEngine {
public:
    SpellCheckerEngine();
    ~SpellCheckerEngine();
    
    // Bulk load operations
    void loadDictionary(const char** words, int count);
    void loadCustomWords(const char** words, int count);
    
    // Incremental operations for custom words
    void addCustomWord(const char* word);
    void removeCustomWord(const char* word);
    
    // Spell checking operations
    bool isCorrect(const char* word) const;
    std::vector<SuggestionResult> getSuggestions(const char* word, int maxDistance) const;
    
    // Helper to check if a word exists in either trie
    bool existsInDictionary(const char* word) const;
    bool existsInCustom(const char* word) const;

private:
    TrieNode* dictionaryTrie;
    TrieNode* customTrie;
    
    // Helper functions
    void bulkInsert(TrieNode* root, const char** words, int count);
    void insertWord(TrieNode* root, const std::string& word);
    bool removeWordRecursive(TrieNode* node, const std::string& word, size_t depth);
    bool searchWord(TrieNode* root, const std::string& word) const;
    void searchSuggestions(TrieNode* node, char letter, const std::string& target,
                          const std::vector<int>& prevRow, int maxCost,
                          std::string currentWord, std::vector<SuggestionResult>& results) const;
    std::string toLowerCase(const std::string& str) const;
    void deleteTrieNodes(TrieNode* node);
};

#endif // SPELL_CHECKER_ENGINE_H