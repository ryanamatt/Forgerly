# **Spell Checker Algorithm**

## **Normal Trie-Based Spell Checking with Levenshtein Distance**

```PseudoCode
{ 1. Insertion into Trie }  
procedure Insert(root, word):  
    curr := root;  
    for char c in word do begin  
        index := c - 'a';  
        if (curr.children[index] == null) then  
            curr.children[index] := new TrieNode();  
        curr := curr.children[index];  
    end  
    curr.isEndOfWord := true;  
end

{ 2. Search with Levenshtein Pruning }  
procedure SearchSuggestions(node, letter, target, prevRow, maxCost, currentWord):  
    size := length(target);  
    currentRow := array of size + 1;  
    currentRow[0] := prevRow[0] + 1;

    { Calculate row values based on Levenshtein Edit Distance }  
    for i := 1 to size do begin  
        insertCost := currentRow[i-1] + 1;  
        deleteCost := prevRow[i] + 1;  
        replaceCost := (target[i-1] == letter) ? prevRow[i-1] : prevRow[i-1] + 1;  
          
        currentRow[i] := min(insertCost, deleteCost, replaceCost);  
    end

    { If word is within cost and valid, record as suggestion }  
    if (currentRow[size] <= maxCost and node.isEndOfWord) then  
        results.add(currentWord, currentRow[size]);

    { Pruning: Only traverse deeper if the row has potential matches }  
    if (min(currentRow) <= maxCost) then begin  
        for i := 0 to 25 do begin  
            if (node.children[i] != null) then  
                SearchSuggestions(node.children[i], 'a' + i, target, currentRow,   
                                  maxCost, currentWord + char(i));  
        end  
    end  
end
```

## **Design Decisions (Forgerly vs. Standard)**

| Change | Rationale |
| :---- | :---- |
| **Dual Trie Architecture** | Separate Tries for dictionary and custom words allow for instant lookup of user-defined character names without polluting the base language dictionary. |
| **Priority Check** | The isCorrect check queries the customTrie first, optimizing for world-building terms which are most likely to trigger false positives in standard dictionaries. |
| **Matrix Pruning** | Standard Levenshtein calculation is $O(M \times N)$; by pruning the Trie traversal when the minimum row value exceeds maxCost, we reduce the search space by orders of magnitude for real-time UI responsiveness. |
| **Memory Lifecycle** | The C++ engine utilizes a recursive deleteTrieNodes pattern triggered by the Python __del__ wrapper, ensuring high-frequency spell checks don't lead to memory bloat in long-running desktop sessions. |

## **Optimization Overview**

The algorithm prioritizes **Suggestions over Verification**. While simple verification is $O(L)$, the generation of fuzzy matches uses a recursive depth-first search. The use of the prevRow pass-down technique avoids re-calculating the entire Levenshtein matrix for every node, effectively turning the suggestion process into a incremental cost calculation.

*Last Updated: 2025-1-13*