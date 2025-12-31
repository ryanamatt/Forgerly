# **🌉 C++ Bridge API Reference**

This document serves as the technical reference for the bridge between the **Python frontend** and the **C++ Core Library (nf\_core\_lib)**. It outlines the data exchange protocol and the mandatory usage patterns for developers.

## **1\. Architecture Overview**

Narrative Forge uses a hybrid architecture to balance UI flexibility with computational performance.

* **Frontend (Python/PyQt6):** Handles user interaction, database management, and UI rendering.  
* **Bridge (nf\_core\_wrapper.py):** Uses cffi to load the shared library and map C-style structs to Python objects.  
* **Core (C++17):** High-performance engines for graph theory (Relationship Layout) and text analysis (Statistics).

## **2\. Shared Data Structures**

These structs are defined in graph\_layout\_engine.h and mirrored in the \_ffi.cdef section of the Python wrapper.

### **Node Input / Output**

Used to pass character positions to the layout engine and retrieve the calculated results.

```C++
struct NodeInput {  
    int id;         // Character ID from SQLite  
    double x\_pos;   // Current X coordinate  
    double y\_pos;   // Current Y coordinate  
    bool is\_fixed;  // If true, the engine calculates forces but doesn't move the node  
};

struct NodeOutput {  
    int id;  
    double x\_pos;  
    double y\_pos;  
};

### **Edge Input**

Used to define the "spring" forces between characters.

struct EdgeInput {  
    int node\_a\_id;  
    int node\_b\_id;  
    double intensity; // 1-100 score used to scale attraction  
};
```

## **3\. Exported C-API Functions**

The library exports functions with extern "C" linkage in nf\_c\_api.cpp to prevent name mangling. These are the low-level entry points.

### **Text Analysis**

| Function | Description | Returns |
| :---- | :---- | :---- |
| calculate\_word\_count | Replicates Python .split() logic in C++. | int |
| calculate\_character\_count | Counts total bytes or non-whitespace bytes. | int |
| calculate\_read\_time | Calculates reading time string (e.g., "5 min"). | const char\* |

### **Graph Layout**

| Function | Description | Returns |
| :---- | :---- | :---- |
| graph\_layout\_create | Initializes a GraphLayoutEngine instance. | void\* (Handle) |
| graph\_layout\_compute | Runs the Fruchterman-Reingold iterations. | int (Status) |
| graph\_layout\_free | Destroys the C++ object and frees memory. | void |

## **4\. Memory Management & Safety**

To prevent memory leaks and segmentation faults, the bridge follows these strict rules:

1. **Allocation:** Python is responsible for allocating the memory for output arrays (e.g., NodeOutput\[\]) before calling the compute functions.  
2. **Strings:** Strings returned from C++ (like calculate\_read\_time) are allocated via strdup. The Python wrapper ensures these are wrapped in ffi.gc or manually freed to avoid leaks.  
3. **Handles:** The void\* handle returned by create functions must always be paired with a free call to prevent memory bloating in the C++ heap.

## **5\. Mandatory Workflow (Python)**

**⚠️ CRITICAL:** Never call \_clib or raw C functions directly within the UI or Repository layers. You must always use the **friendly Python functions** provided in nf\_core\_wrapper.py.

The wrapper manages the lifecycle of C++ objects, handles pointer arithmetic, and performs the necessary data conversions.

### **Example: Relationship Layout**

Instead of manually managing pointers, use the GraphLayoutWrapper class:

```Python
from src.python.utils.nf_core_wrapper import GraphLayoutEngineWrapper

engine = GraphLayoutEngineWrapper(nodes_input, edges_input, width, height)
            
new_positions = engine.compute_layout(max_iterations=200, initial_temperature=init_temp)

self._update_node_positions(new_positions)

### **Example: Text Statistics**

Use the simple functional interface for immediate calculations:

from src.python.utils.nf_core_wrapper import calculate_read_time

# The wrapper handles char* conversion and string memory cleanup  
read_time = calculate_read_time(word_count, wpm) 
print(f"Reading Time: {read_time}")

```

*Last Updated: 2025-12-21*