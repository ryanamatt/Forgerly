// src/c_lib/spell_checker/trie.h

#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <algorithm>

struct TrieNode {
    TrieNode* children[26];
    bool isEndOfWord = false;
    
    TrieNode() {
        for (int i = 0; i< 26; i++) children[i] = nullptr;
        isEndOfWord = false;
    }
};

// Function to insert a word into the Trie
void insert(TrieNode* root, std::string word) {
    TrieNode* curr = root;
    for (char c : word) {
        int index = c - 'a';
        if (!curr->children[index]) {
            curr->children[index] = new TrieNode();
        }
        curr = curr->children[index];
    }
    curr->isEndOfWord = true;
}

// Recursive search for Levenshtein distance
void searchRecursive(TrieNode* node, char letter, const std::string& target, 
                     const std::vector<int>& prevRow, int maxCost, std::string currentWord) {
    int size = target.size();
    std::vector<int> currentRow(size + 1);
    currentRow[0] = prevRow[0] + 1;

    // Calculate the Levenshtein row for this node
    for (int i = 1; i <= size; ++i) {
        int insertCost = currentRow[i - 1] + 1;
        int deleteCost = prevRow[i] + 1;
        int replaceCost = (target[i - 1] == letter) ? prevRow[i - 1] : prevRow[i - 1] + 1;

        currentRow[i] = std::min({insertCost, deleteCost, replaceCost});
    }

    // If the last element in the row is within maxCost, and it's a word, add it
    if (currentRow[size] <= maxCost && node->isEndOfWord) {
        std::cout << "Suggestion: " << currentWord << " (Dist: " << currentRow[size] << ")\n";
    }

    // PRUNING: Only continue if some value in currentRow is <= maxCost
    if (*std::min_element(currentRow.begin(), currentRow.end()) <= maxCost) {
        for (int i = 0; i < 26; i++) {
            if (node->children[i]) {
                searchRecursive(node->children[i], 'a' + i, target, currentRow, maxCost, currentWord + (char)('a' + i));
            }
        }
    }
}