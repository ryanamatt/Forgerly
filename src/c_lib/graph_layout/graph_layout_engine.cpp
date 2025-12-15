// src/c_lib/graph_layout.cpp

#include "graph_layout_engine.h"
#include <iostream>

// --- Constants ---
const double C_ATTRACTION = 1.0;
const double C_REPEL = 1.0;
const double C_COOLING = 0.99;
const double MIN_DIST = 0.01; // Avoid division by 0

// --- Public Constructor and Main Method ---

GraphLayoutEngine::GraphLayoutEngine(const std::vector<NodeInput>& nodes, 
                                     const std::vector<EdgeInput>& edges,
                                     double width, double height)
    : input_nodes_(nodes), 
      input_edges_(edges),
      W_(width),
      H_(height),
      t_(0.0) 
{
    // Calculate Parameters based on the number of nodes (N) and area (A)
    area_ = W_ * H_;
    // k = sqrt(Area / N)
    if (!nodes.empty()) {
        k_ = C_ATTRACTION * std::sqrt(area_ / nodes.size());
    } else {
        k_ = 1.0; // Default to Safe Value
    }
}

// --- Fruchterman-Reingold Force Functions ---

// Attractive Force f_a(d) = d^2 / k
double GraphLayoutEngine::force_attr(double dist) const {
    if (dist < MIN_DIST) return 0.0;
    return (dist * dist) / k_;
}

// Repulsive Force f_r(d) = k^2 / d
double GraphLayoutEngine::force_rep(double dist) const {
    if (dist < MIN_DIST) return 1000.0; // High Force if too close
    return (k_ * k_) / dist;
}

double GraphLayoutEngine::distance(double x1, double y1, double x2, double y2) const {
    return std::sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1));
}

// --- Initialization ---

void GraphLayoutEngine::initialize_positions() {
    std::random_device rd;
    std::mt19937 gen(rd());
    // Use a distribution for the canvas size (e.g. -W/2 to W/2)
    std::uniform_real_distribution<> distrib_x(-W_ / 2.0, W_ / 2.0);
    std::uniform_real_distribution<> distrib_y(-H_ / 2.0, H_ / 2.0);

    for (const auto& node : input_nodes_) {
        NodeOutput pos;
        pos.id = node.id;

        if (node.is_fixed) {
            pos.x_pos = node.x_pos;
            pos.y_pos = node.y_pos;
        } else {
            pos.x_pos = distrib_x(gen);
            pos.y_pos = distrib_y(gen);
        }
        node_positions_[node.id] = pos;
    }
}

// --- Core Algorithm Steps ---

void GraphLayoutEngine::apply_repulsive_forces() {
    // Stores the displacement vector for each node. Reset for this iteration.
    node_displacements_.clear();
    for (const auto& node : input_nodes_) {
        // Initialize displacement for all nodes
        node_displacements_[node.id] = {0.0, 0.0}; 
    }

    // O(N^2) loop for all pairs of nodes (bottleneck for large N)
    for (size_t i = 0; i < input_nodes_.size(); ++i) {
        int u_id = input_nodes_[i].id;

        for (size_t j = i + 1; j < input_nodes_.size(); ++j) {
            int v_id = input_nodes_[j].id;

            const auto& u_pos = node_positions_[u_id];
            const auto& v_pos = node_positions_[v_id];

            double delta_x = u_pos.x_pos - v_pos.x_pos;
            double delta_y = u_pos.y_pos - v_pos.y_pos;
            double dist = distance(u_pos.x_pos, u_pos.y_pos, v_pos.x_pos, v_pos.y_pos);

            // Calculate repulsive force magnitude
            double force = force_rep(dist);

            // Calculate the repulsive vector components
            double dx = delta_x / dist * force * C_REPEL;
            double dy = delta_y / dist * force * C_REPEL;

            // Apply displacement: Nodes push away from each other
            if (!input_nodes_[i].is_fixed) {
                node_displacements_[u_id].x += dx; // Push u away from v
                node_displacements_[u_id].y += dy;
            }
            
            if (!input_nodes_[j].is_fixed) {
                node_displacements_[v_id].x -= dx; // Push v away from u
                node_displacements_[v_id].y -= dy;
            }
        }
    }
    
    // Update node positions based on repulsive displacements
    for (auto& pair : node_positions_) {
        int id = pair.first;
        if (!input_nodes_[id].is_fixed) {
            // Apply displacement limited by temperature (t_)
            double disp_x = node_displacements_[id].x;
            double disp_y = node_displacements_[id].y;
            double disp_mag = std::sqrt(disp_x*disp_x + disp_y*disp_y);

            // Limit displacement by current temperature and apply
            pair.second.x_pos += disp_x / disp_mag * std::min(disp_mag, t_);
            pair.second.y_pos += disp_y / disp_mag * std::min(disp_mag, t_);
        }
    }
}

void GraphLayoutEngine::apply_attractive_forces() {
    // O(M) loop, where M is the number of edges
    for (const auto& edge : input_edges_) {
        int u_id = edge.node_a_id;
        int v_id = edge.node_b_id;

        const auto& u_pos = node_positions_[u_id];
        const auto& v_pos = node_positions_[v_id];

        double delta_x = u_pos.x_pos - v_pos.x_pos;
        double delta_y = u_pos.y_pos - v_pos.y_pos;
        double dist = distance(u_pos.x_pos, u_pos.y_pos, v_pos.x_pos, v_pos.y_pos);

        // Calculate attractive force magnitude, scaled by intensity
        double force = force_attr(dist) * (edge.intensity / 100.0); // Normalize intensity 0-1

        // Calculate the attractive vector components
        double dx = delta_x / dist * force * C_ATTRACTION;
        double dy = delta_y / dist * force * C_ATTRACTION;

        // Apply displacement: Nodes pull towards each other
        if (!input_nodes_[u_id].is_fixed) {
            node_displacements_[u_id].x -= dx; // Pull u towards v
            node_displacements_[u_id].y -= dy;
        }

        if (!input_nodes_[v_id].is_fixed) {
            node_displacements_[v_id].x += dx; // Pull v towards u
            node_displacements_[v_id].y += dy;
        }
    }
    
    // Update node positions based on combined displacements (Repulsive + Attractive)
    for (auto& pair : node_positions_) {
        int id = pair.first;
        if (!input_nodes_[id].is_fixed) {
            // Re-apply displacement limiting using the combined force vector.
            double disp_x = node_displacements_[id].x;
            double disp_y = node_displacements_[id].y;
            double disp_mag = std::sqrt(disp_x*disp_x + disp_y*disp_y);

            // Limit displacement by current temperature and apply
            pair.second.x_pos += disp_x / disp_mag * std::min(disp_mag, t_);
            pair.second.y_pos += disp_y / disp_mag * std::min(disp_mag, t_);
        }
    }
}

void GraphLayoutEngine::cool_down() {
    t_ *= C_COOLING;
}

std::vector<NodeOutput> GraphLayoutEngine::computeLayout(int max_iterations, double initial_temperature) {
    if (input_nodes_.empty()) return {};

    t_ = initial_temperature;
    initialize_positions();

    for (int iter = 0; iter < max_iterations; iter++) {
        apply_repulsive_forces();
        apply_attractive_forces();

        cool_down();
    }

    std::vector<NodeOutput> final_positions;
    for (const auto& pair : node_positions_) {
        final_positions.push_back(pair.second);
    }
    return final_positions;
}

int main ()
{
    return 0;
}