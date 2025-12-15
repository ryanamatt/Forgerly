// src/c_lib/nf_c_api.cpp
// This file acts as the consolidated C-API bridge for the entire nf_core_lib.dll

#include "text_stats/text_stats_engine.h"
#include "graph_layout/graph_layout_engine.h"
#include <cstring>
#include <string>
#include <vector>
#include <sstream>
#include <stdexcept>
#include <iostream>

extern "C" {

/**
 * @brief C-API wrapper for calculate_word_count_c.
 */
int calculate_word_count(const char* text) {
    // Direct call to the existing C++-backed C function
    return calculate_word_count_c(text);
}

/**
 * @brief C-API wrapper for calculate_character_count_c.
 */
int calculate_character_count(const char* text, int include_spaces) {
    // Direct call to the existing C++-backed C function
    return calculate_character_count_c(text, include_spaces);
}

/**
 * @brief C-API wrapper for calculate_read_time_c.
 * NOTE: The Python caller is responsible for freeing the returned string (const char*).
 */
const char* calculate_read_time(int word_count, int wpm) {
    // Direct call to the existing C++-backed C function
    return calculate_read_time_c(word_count, wpm);
}

// --- Graph Layout Engine C-API Wrappers ---

// Opaque pointer for the GraphLayoutEngine class instance
using GraphLayoutHandle = void*;

/**
 * @brief Creates a new GraphLayoutEngine instance.
 * @param node_data A pointer to the array of NodeInput structures.
 * @param node_count The number of elements in the node_data array.
 * @param edge_data A pointer to the array of EdgeInput structures.
 * @param edge_count The number of elements in the edge_data array.
 * @param width The width of the simulation area.
 * @param height The height of the simulation area.
 * @return An opaque handle (void*) to the new GraphLayoutEngine object.
 */
GraphLayoutHandle graph_layout_create(
    const NodeInput* node_data, int node_count,
    const EdgeInput* edge_data, int edge_count,
    double width, double height) 
{
    // Convert C-style arrays to C++ std::vector
    std::vector<NodeInput> nodes(node_data, node_data + node_count);
    std::vector<EdgeInput> edges(edge_data, edge_data + edge_count);

    // Create the C++ object on the heap
    try {
        GraphLayoutEngine* engine = new GraphLayoutEngine(nodes, edges, width, height);
        // Return the pointer as an opaque handle
        return static_cast<GraphLayoutHandle>(engine);
    } catch (const std::exception& e) {
        // Handle allocation or initialization error (simplified for C-API)
        std::cerr << "Error creating GraphLayoutEngine: " << e.what() << std::endl;
        return nullptr;
    }
}

/**
 * @brief Destroys a GraphLayoutEngine instance, freeing its memory.
 * @param handle The opaque handle to the GraphLayoutEngine object.
 */
void graph_layout_destroy(GraphLayoutHandle handle) {
    if (handle) {
        // Cast the void* back to the correct C++ pointer type and delete it
        delete static_cast<GraphLayoutEngine*>(handle);
    }
}

/**
 * @brief Computes the layout and returns the resulting node positions.
 * @param handle The opaque handle to the GraphLayoutEngine object.
 * @param max_iterations The maximum number of iterations for the algorithm.
 * @param initial_temperature The starting temperature for the simulation.
 * @param output_array Pointer to a pre-allocated array of NodeOutput for results.
 * @param output_count Pointer to store the number of elements written to output_array.
 * @return 0 on success, -1 on failure (e.g., null handle).
 */
int graph_layout_compute(
    GraphLayoutHandle handle,
    int max_iterations, 
    double initial_temperature,
    NodeOutput* output_array,
    int* output_count)
{
    if (!handle || !output_array || !output_count) {
        *output_count = 0;
        return -1; // Indicate failure
    }

    GraphLayoutEngine* engine = static_cast<GraphLayoutEngine*>(handle);

    // Call the core C++ method
    std::vector<NodeOutput> results = engine->computeLayout(max_iterations, initial_temperature);

    // Copy results back to the C-style array provided by the caller (Python)
    size_t count = results.size();
    if (count > 0) {
        std::copy(results.begin(), results.end(), output_array);
    }

    *output_count = static_cast<int>(count);
    return 0; // Indicate success
}

} // extern "C"