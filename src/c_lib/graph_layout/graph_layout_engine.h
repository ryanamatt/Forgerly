// src/python/graph_layout_engine.h

#ifndef GRAPH_LAYOUT_ENGINE_H
#define GRAPH_LAYOUT_ENGINE_H

#include <vector>
#include <map>
#include <cmath>
#include <algorithm>
#include <random>

struct Point {
    double x;
    double y;
};

// --- Data Structures for Exchage

// Represents an input Node
struct NodeInput {
    int id;         // Character ID
    double x_pos;   // Initial/Fixed X Positon
    double y_pos;   // Initial/Fixed Y Position
    bool is_fixed;  // Flag to prevent movement (if user pinned it)
};

// Represents an input edge (Relationship)
struct EdgeInput {
    int node_a_id;      // Character_A_ID
    int node_b_id;      // Character_B_ID
    double intensity;   // 1-100 score, used to scale attraction force
};

// Represents the output positiion of a node
struct NodeOutput {
    int id;           // Character_ID
    double x_pos;     // Final X Position
    double y_pos;     // Final Y_Position
};


// --- Main Layout Class ---

class GraphLayoutEngine {
public:
    GraphLayoutEngine(const std::vector<NodeInput>& nodes,
                    const std::vector<EdgeInput>& edges,
                    double width, double height);
    
    std::vector<NodeOutput> computeLayout(int max_iterations=100, double initial_temperature=5.0);

private:
    // Core Data
    std::vector<NodeInput> input_nodes_;
    std::vector<EdgeInput> input_edges_;
    std::map<int, NodeOutput> node_positions_; // Stores current X, Y for calculation
    std::map<int, Point> node_displacements_; // Stores temporary displacement vectors
    std::map<int, bool> is_fixed_map_;

    // Simulation Parameters
    double W_; // Width of the simulation area (e.g., QGraphicsView size)
    double H_; // Height of the simulation area
    double area_;
    double k_; // Optimal distance parameter

    // Internal simulation state
    double t_; // Current temperature (controls movement scale)

    // Private Helper functions for Fruchtermen-Reingold algorithm
    void initialize_positions();
    void apply_repulsive_forces();
    void apply_attractive_forces();
    void update_positions();
    void limit_displacement(double max_disp);
    void cool_down();
    double distance(double x1, double y1, double x2, double y2) const;

    // Fruchterman-Reingold force functions
    double force_attr(double dist) const;
    double force_rep(double dist) const;
};

#endif