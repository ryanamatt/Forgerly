# src/python/utils/graph_layout.py
from .ffi_base import ffi, lib

# Append graph-specific definitions
ffi.cdef("""
    typedef struct {
        int id;
        double x_pos;
        double y_pos;
        bool is_fixed;
    } NodeInput;

    typedef struct {
        int node_a_id;
        int node_b_id;
        double intensity;
    } EdgeInput;

    typedef struct {
        int id;
        double x_pos;
        double y_pos;
    } NodeOutput;

    typedef void* GraphLayoutHandle;

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

class GraphLayoutEngineWrapper:
    def __init__(self, nodes: list, edges: list, width: float, height: float) -> None:
        self._node_count = len(nodes)
        self._width = width
        self._height = height
        
        # Use shared ffi to allocate memory
        self._node_c_array = ffi.new("NodeInput[]", self._node_count)
        
        offset_x = width / 2.0
        offset_y = height / 2.0       
        
        for i, node in enumerate(nodes):
            self._node_c_array[i].id = node['id']
            self._node_c_array[i].x_pos = node['x_pos'] - offset_x
            self._node_c_array[i].y_pos = node['y_pos'] - offset_y
            self._node_c_array[i].is_fixed = bool(node.get('is_fixed', False))

        self._edge_count = len(edges)
        self._edge_c_array = ffi.new("EdgeInput[]", self._edge_count)
        for i, edge in enumerate(edges):
            self._edge_c_array[i].node_a_id = edge['node_a_id']
            self._edge_c_array[i].node_b_id = edge['node_b_id']
            self._edge_c_array[i].intensity = edge.get('intensity', 50.0)

        self._handle = lib.graph_layout_create(
            self._node_c_array, self._node_count,
            self._edge_c_array, self._edge_count,
            width, height
        )

        if not self._handle:
            raise RuntimeError("Failed to create C++ GraphLayoutEngine instance.")

    def __del__(self) -> None:
        if hasattr(self, '_handle') and self._handle:
            lib.graph_layout_destroy(self._handle)
            self._handle = None

    def compute_layout(self, max_iterations: int = 100, initial_temperature: float = 5.0) -> list[dict]:
        if not self._handle or self._node_count == 0:
            return []

        output_c_array = ffi.new("NodeOutput[]", self._node_count)
        output_count_ptr = ffi.new("int*", 0)

        result_code = lib.graph_layout_compute(
            self._handle, max_iterations, initial_temperature,
            output_c_array, output_count_ptr
        )

        if result_code != 0:
            return []

        final_positions = []
        actual_count = output_count_ptr[0]
        offset_x = self._width / 2.0
        offset_y = self._height / 2.0
        
        for i in range(actual_count):
            final_positions.append({
                'id': output_c_array[i].id,
                'x_pos': output_c_array[i].x_pos + offset_x,
                'y_pos': output_c_array[i].y_pos + offset_y,
            })

        return final_positions