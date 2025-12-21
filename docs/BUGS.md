# Known Bugs

## Bug Template

### 🏷️ [Short Descriptive Title]

**Status:** 🔴 New | 🟡 In Progress | 🟢 Fixed  
**Severity:** Low | Medium | High | Critical  

- **The Issue:** What is happening? (e.g., "The relationship edge doesn't update when a node is moved via C++ auto-layout.")
- **How to Reproduce:**
    1. Open the Relationship Graph.
    2. Click 'Auto-Layout'.
    3. Observe that edges remain in their old positions until a node is clicked manually.
- **Expected Behavior:** Edges should stay attached to nodes during the layout animation.
- **Technical Notes:** Check if the C++ wrapper is emitting the `node_moved` signal for every frame or only at the end of the calculation.

## List of Known Bugs
