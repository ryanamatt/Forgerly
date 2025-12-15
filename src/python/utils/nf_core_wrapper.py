# src/python/utils/nf_core_wrapper.py

import os
import sys
from cffi import FFI

# --- Configuration ---
# Define the C library name based on the target OS
if sys.platform.startswith('win'):
    _LIB_NAME = "nf_core_lib.dll"
elif sys.platform.startswith('linux'):
    _LIB_NAME = "nf_core_lib.so"
elif sys.platform.startswith('darwin'):
    _LIB_NAME = "nf_core_lib.dylib"
else:
    _LIB_NAME = "nf_core_lib.so" 

_ffi = FFI()
_clib = None

# Declare ALL functions from the C++ library here.
_ffi.cdef("""
    // --- Data Structures for Exchange ---
    typedef struct {
        double x;
        double y;
    } Point; // Not directly used in API, but good for context

    typedef struct {
        int id;         // Character ID
        double x_pos;   // Initial/Fixed X Positon
        double y_pos;   // Initial/Fixed Y Position
        bool is_fixed;  // Flag to prevent movement (if user pinned it)
    } NodeInput;

    typedef struct {
        int node_a_id;      // Character_A_ID
        int node_b_id;      // Character_B_ID
        double intensity;   // 1-100 score, used to scale attraction force
    } EdgeInput;

    typedef struct {
        int id;           // Character_ID
        double x_pos;     // Final X Position
        double y_pos;     // Final Y_Position
    } NodeOutput;

    // --- Text Stats Engine C-API functions (prefixed in C for clarity) ---
    int calculate_word_count(const char* text);
    int calculate_character_count(const char* text, int include_spaces);
    const char* calculate_read_time(int word_count, int wpm);

    // --- Graph Layout Engine C-API functions ---
    typedef void* GraphLayoutHandle; // Opaque pointer to C++ GraphLayoutEngine

    GraphLayoutHandle graph_layout_create(
        const NodeInput* node_data, int node_count,
        const EdgeInput* edge_data, int edge_count,
        double width, double height);

    void graph_layout_destroy(GraphLayoutHandle handle);

    int graph_layout_compute(
        GraphLayoutHandle handle,
        int max_iterations,
        double initial_temperature,
        NodeOutput* output_array,
        int* output_count);

""")

try:
    # Attempt to load the library from a relative path
    _lib_path_local = os.path.join(os.path.dirname(__file__), '..', '..', 'c_lib', _LIB_NAME)
    
    # Load the C Library
    try:
        _clib = _ffi.dlopen(_lib_path_local)
    except OSError:
        # Fallback to loading from system path
        _clib = _ffi.dlopen(_LIB_NAME)

except Exception as e:
    error_msg = (f"CRITICAL: Failed to load C++ core library ({_LIB_NAME}). "
                 f"Ensure the C++ library is compiled and available. Error: {e}")
    raise ImportError(error_msg)


# --- Public Wrapper Functions ---

def calculate_word_count(text: str) -> int:
    """
    Calculates the word count using the C++ engine.
    
    :param text: The text to calculate word count for.
    :type text: str

    :returns: The word count
    :rtype: int
    """
    # Convert Python string to C bytes (UTF-8)
    text_bytes = text.encode('utf-8')
    return _clib.calculate_word_count(text_bytes)

def calculate_character_count(text: str, include_spaces: bool = True) -> int:
    """
    Calculates the character count using the C++ engine.
    
    :param text: The text to calculate character count for.
    :type text: str
    :param includes_spaces: Bool value to count spaces as characters, Default is True.
    :type includes_spaces: bool

    :returns: The character count
    :rtype: int
    """
    text_bytes = text.encode('utf-8')
    c_include_spaces = 1 if include_spaces else 0
    return _clib.calculate_character_count(text_bytes, c_include_spaces)

def calculate_read_time(word_count: int, wpm: int = 250) -> str:
    """
    Calculates the estimated read time using the C++ engine.
    
    :param word_count: The word count.
    :type word_count: int
    :param wpm: The words per minute, Default is 250.
    :type wpm: int

    :returns: The calculated read time. Format: "{int} min"
    :rtype: str
    """
    result_ptr = _clib.calculate_read_time(word_count, wpm)
    
    if result_ptr:
        # cffi automatically handles the const char* to Python bytes conversion
        result_str = _ffi.string(result_ptr).decode('utf-8')
        
        # Read time functions used strdup(), which must be freed.
        return result_str
    return "0 min"


# --- Graph Layout ---

class GraphLayoutEngineWrapper:
    """
    Python wrapper for the C++ GraphLayoutEngine, managing its lifecycle
    using an opaque C handle.
    """
    def __init__(self, nodes: list, edges: list, width: float, height: float) -> None:
        """
        Initializes the C++ layout engine and converts input lists to C arrays.

        :param nodes: List of NodeInput dicts/objects.
        :type nodes: list[NodeInput]
        :param edges: List of EdgeInput dicts/objects.
        :type edges: list[EdgeInput]
        :param width: Simulation area width.
        :type: width: float
        :param height: Simulation area height.
        :type height: float

        :rtype: None
        """
        # 1. Convert Python lists/dicts into CFFI C arrays
        
        # Create C arrays for NodeInput
        self._node_count = len(nodes)
        self._node_c_array = _ffi.new("NodeInput[]", self._node_count)
        
        # NOTE: Assumes 'nodes' is a list of dictionaries like 
        # {'id': 1, 'x_pos': 0.0, 'y_pos': 0.0, 'is_fixed': False}
        for i, node in enumerate(nodes):
            self._node_c_array[i].id = node['id']
            self._node_c_array[i].x_pos = node['x_pos']
            self._node_c_array[i].y_pos = node['y_pos']
            self._node_c_array[i].is_fixed = bool(node.get('is_fixed', False))

        # Create C arrays for EdgeInput
        self._edge_count = len(edges)
        self._edge_c_array = _ffi.new("EdgeInput[]", self._edge_count)
        for i, edge in enumerate(edges):
            self._edge_c_array[i].node_a_id = edge['node_a_id']
            self._edge_c_array[i].node_b_id = edge['node_b_id']
            self._edge_c_array[i].intensity = edge.get('intensity', 50.0) # Default intensity

        # 2. Create the C++ Engine instance
        self._handle = _clib.nf_graph_layout_create(
            self._node_c_array, self._node_count,
            self._edge_c_array, self._edge_count,
            width, height
        )

        if not self._handle:
            raise RuntimeError("Failed to create C++ GraphLayoutEngine instance.")

    def __del__(self) -> None:
        """
        Ensures the C++ object is destroyed when the Python object is garbage collected.
        
        :rtype: None
        """
        if self._handle:
            _clib.nf_graph_layout_destroy(self._handle)
            self._handle = None # Clear the handle

    def compute_layout(self, max_iterations: int = 100, initial_temperature: float = 5.0) -> list[dict]:
        """
        Runs the Fruchterman-Reingold algorithm and returns the final positions.

        :param max_iterations: Then number of iterations to run the algorithm for. Default 100.
        :type max_iterations: int
        :param initial_temperature: THe inital temperature of the algorithm. Default 5.0.
        :type initial_temperature: float

        :returns: List of NodeOutput dicts: [{'id': 1, 'x_pos': 10.5, 'y_pos': 20.3}, ...]
        :rtype: list[dict]
        """
        if not self._handle or self._node_count == 0:
            return []

        # 1. Allocate memory for the output C array (must be large enough)
        output_c_array = _ffi.new("NodeOutput[]", self._node_count)
        
        # CFFI pointer to hold the actual count of results written
        output_count_ptr = _ffi.new("int*", 0)

        # 2. Call the C computation function
        result_code = _clib.nf_graph_layout_compute(
            self._handle,
            max_iterations,
            initial_temperature,
            output_c_array,
            output_count_ptr
        )

        if result_code != 0:
            print("Warning: Graph layout computation failed in C-API.")
            return []

        # 3. Convert C output array back to a list of Python dictionaries
        final_positions = []
        actual_count = output_count_ptr[0]
        
        for i in range(actual_count):
            final_positions.append({
                'id': output_c_array[i].id,
                'x_pos': output_c_array[i].x_pos,
                'y_pos': output_c_array[i].y_pos,
            })

        return final_positions