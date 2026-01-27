// src/c_lib/spell_checker/spell_checker_engine.cpp

#include "spell_checker_engine.h"
#include "trie.h"
#include <algorithm>
#include <cctype>
#include <iostream>

SpellCheckerEngine::SpellCheckerEngine() {
    dictionaryTrie = new TrieNode();
    customTrie = new TrieNode();
}

SpellCheckerEngine::~SpellCheckerEngine() {
    deleteTrieNodes(dictionaryTrie);
    deleteTrieNodes(customTrie);
}

void SpellCheckerEngine::deleteTrieNodes(TrieNode* node) {
    if (!node) return;
    for (int i = 0; i < 26; i++) {
        if (node->children[i]) {
            deleteTrieNodes(node->children[i]);
        }
    }
    delete node;
}

void SpellCheckerEngine::loadDictionary(const char** words, int count) {
    bulkInsert(dictionaryTrie, words, count);
}

void SpellCheckerEngine::loadCustomWords(const char ** words, int count) {
    bulkInsert(customTrie, words, count);
}

void SpellCheckerEngine::addCustomWord(const char* word) {
    if (word && word[0] != '\0') {
        std::string normalized = toLowerCase(word);
        insertWord(customTrie, normalized);
    }
}

void SpellCheckerEngine::removeCustomWord(const char* word) {
    if (!word || word[0] == '\0') {
        return;
    }
    std::string normalized = toLowerCase(word);
    removeWordRecursive(customTrie, normalized, 0);
}

bool SpellCheckerEngine::isCorrect(const char* word) const {
    if (!word || word[0] == '\0') {
        return false;
    }

    std::string normalized = toLowerCase(word);

    // Check Custom Trie, Higher Priority
    if (searchWord(customTrie, normalized)) {
        return true;
    }

    // Then Search Dictionary
    return searchWord(dictionaryTrie, normalized);
}

std::vector<SuggestionResult> SpellCheckerEngine::getSuggestions(const char* word, int maxDistance) const {
    std::vector<SuggestionResult> results;
    
    if (!word || word[0] == '\0') {
        return results;
    }

    std::string target = toLowerCase(word);

    // Initialize first row of Levenshtein Matrix
    std::vector<int> firstRow(target.size() + 1);
    for (size_t i = 0; i <= target.size(); i++) {
        firstRow[i] = i;
    }

    // Search Custom trie first
    for (int i = 0; i < 26; i++) {
        if (customTrie->children[i]) {
            char c = 'a' + i;
            searchSuggestions(customTrie->children[i], c, target, firstRow, maxDistance, 
                std::string(1, c), results);
        }
    }

    // Search Dictionary Trie
    for (int i = 0; i < 26; i++) {
        if (dictionaryTrie->children[i]) {
            char c = 'a' + i;
            searchSuggestions(dictionaryTrie->children[i], c, target, firstRow, maxDistance, 
                std::string(1, c), results);
        }
    }

    // Sort by distance (closet first), then alphabetically
    std::sort(results.begin(), results.end(), [](const SuggestionResult& a, const SuggestionResult& b) {
        if (a.distance != b.distance) {
            return a.distance < b.distance;
        }
        return a.word < b.word;
    });

    // Remove duplicates (if word exists in both tries)
    auto last = std::unique(results.begin(), results.end(), 
        [](const SuggestionResult& a, const SuggestionResult& b) {
            return a.word == b.word;
        });
    results.erase(last, results.end());
    
    return results;
}

bool SpellCheckerEngine::existsInDictionary(const char* word) const {
    if (!word || word[0] == '\0') {
        return false;
    }
    return searchWord(dictionaryTrie, toLowerCase(word));
}

bool SpellCheckerEngine::existsInCustom(const char* word) const {
    if (!word || word[0] == '\0') {
        return false;
    }
    return searchWord(customTrie, toLowerCase(word));
}

// Private Helper Methods

void SpellCheckerEngine::bulkInsert(TrieNode* root, const char** words, int count) {
    for (int i = 0; i < count; i++) {
        if (words[i] && words[i][0] != '\0') {
            std::string normalized = toLowerCase(words[i]);
            insertWord(root, normalized);
        }
    }
}

void SpellCheckerEngine::insertWord(TrieNode* root, const std::string& word) {
    TrieNode* curr = root;
    for (char c : word) {
        // Only handle lowercase a-z
        if (c < 'a' || c > 'z') {
            continue;
        }
        
        int index = c - 'a';
        if (!curr->children[index]) {
            curr->children[index] = new TrieNode();
        }
        curr = curr->children[index];
    }
    curr->isEndOfWord = true;
}

bool SpellCheckerEngine::removeWordRecursive(TrieNode* node, const std::string& word, size_t depth) {
    if (!node) return false;

    // Base Case: Reach End of Word
    if (depth == word.length()) {
        if (node ->isEndOfWord) {
            node->isEndOfWord = false;
        }

        // Return True if the node hs no children (safe to delete)
        for (int i = 0; i < 26; i++) {
            if (node->children[i]) return false;
        }
        return true;
    }

    // Recursive Case: move down to the next character
    int index = word[depth] - 'a';
    if (index < 0 || index >= 26 || !node->children[index]) {
        return false;
    }

    bool shouldDeleteChild = removeWordRecursive(node->children[index], word, depth + 1);

    if (shouldDeleteChild) {
        delete node->children[index];
        node->children[index] = nullptr;

        // If this node is not the end of another word and has no other children, 
        // tell the parent to delete this node too
        if (!node->isEndOfWord) {
            for (int i = 0; i < 26; i++) {
                if (node->children[i]) return false;
            }
            return true;
        }
    }

    return false;
}

bool SpellCheckerEngine::searchWord(TrieNode* root, const std::string& word) const {
    TrieNode* curr = root;
    for (char c : word) {
        if (c < 'a' || c > 'z') {
            return false;
        }
        
        int index = c - 'a';
        if (!curr->children[index]) {
            return false;
        }
        curr = curr->children[index];
    }
    return curr->isEndOfWord;
}

void SpellCheckerEngine::searchSuggestions(TrieNode* node, char letter, const std::string& target,
                                          const std::vector<int>& prevRow, int maxCost,
                                          std::string currentWord,
                                          std::vector<SuggestionResult>& results) const {
    int size = target.size();
    std::vector<int> currentRow(size + 1);
    currentRow[0] = prevRow[0] + 1;

    // Calculate Levenshtein distance for this row
    for (int i = 1; i <= size; ++i) {
        int insertCost = currentRow[i - 1] + 1;
        int deleteCost = prevRow[i] + 1;
        int replaceCost = (target[i - 1] == letter) ? prevRow[i - 1] : prevRow[i - 1] + 1;
        currentRow[i] = std::min({insertCost, deleteCost, replaceCost});
    }

    // If this is a word and within maxCost, add to results
    if (currentRow[size] <= maxCost && node->isEndOfWord) {
        results.push_back({currentWord, currentRow[size]});
    }

    // Prune: only continue if some value in row is <= maxCost
    if (*std::min_element(currentRow.begin(), currentRow.end()) <= maxCost) {
        for (int i = 0; i < 26; i++) {
            if (node->children[i]) {
                searchSuggestions(node->children[i], 'a' + i, target, currentRow,
                                maxCost, currentWord + (char)('a' + i), results);
            }
        }
    }
}

std::string SpellCheckerEngine::toLowerCase(const std::string& str) const {
    std::string result = str;
    std::transform(result.begin(), result.end(), result.begin(),
                   [](unsigned char c) { return std::tolower(c); });
    return result;
}
