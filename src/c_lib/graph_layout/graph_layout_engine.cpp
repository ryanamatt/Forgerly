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

    initialize_positions();
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
    std::uniform_real_distribution<> distrib_x(-W_ / 2.0, W_ / 2.0);
    std::uniform_real_distribution<> distrib_y(-H_ / 2.0, H_ / 2.0);

    // Clear and rebuild the tracking maps based on input_nodes_
    node_positions_.clear();
    
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
    node_displacements_.clear();
    for (const auto& node : input_nodes_) {
        node_displacements_[node.id] = {0.0, 0.0}; 
    }

    for (size_t i = 0; i < input_nodes_.size(); ++i) {
        int u_id = input_nodes_[i].id;
        bool u_fixed = input_nodes_[i].is_fixed;

        for (size_t j = i + 1; j < input_nodes_.size(); ++j) {
            int v_id = input_nodes_[j].id;
            bool v_fixed = input_nodes_[j].is_fixed;

            const auto& u_pos = node_positions_[u_id];
            const auto& v_pos = node_positions_[v_id];

            double delta_x = u_pos.x_pos - v_pos.x_pos;
            double delta_y = u_pos.y_pos - v_pos.y_pos;
            double dist = distance(u_pos.x_pos, u_pos.y_pos, v_pos.x_pos, v_pos.y_pos);

            double force = force_rep(dist);
            double dx = (delta_x / dist) * force * C_REPEL;
            double dy = (delta_y / dist) * force * C_REPEL;

            if (!u_fixed) {
                node_displacements_[u_id].x += dx;
                node_displacements_[u_id].y += dy;
            }
            if (!v_fixed) {
                node_displacements_[v_id].x -= dx;
                node_displacements_[v_id].y -= dy;
            }
        }
    }
}

void GraphLayoutEngine::apply_attractive_forces() {
    for (const auto& edge : input_edges_) {
        int u_id = edge.node_a_id;
        int v_id = edge.node_b_id;

        // Find the fixed status for these specific IDs safely
        bool u_fixed = false;
        bool v_fixed = false;
        for (const auto& n : input_nodes_) {
            if (n.id == u_id) u_fixed = n.is_fixed;
            if (n.id == v_id) v_fixed = n.is_fixed;
        }

        const auto& u_pos = node_positions_[u_id];
        const auto& v_pos = node_positions_[v_id];

        double delta_x = u_pos.x_pos - v_pos.x_pos;
        double delta_y = u_pos.y_pos - v_pos.y_pos;
        double dist = distance(u_pos.x_pos, u_pos.y_pos, v_pos.x_pos, v_pos.y_pos);

        double force = force_attr(dist) * (edge.intensity / 10.0); // Ensures Repulsion is Stronger than Attraction
        double dx = (delta_x / dist) * force * C_ATTRACTION;
        double dy = (delta_y / dist) * force * C_ATTRACTION;

        if (!u_fixed) {
            node_displacements_[u_id].x -= dx;
            node_displacements_[u_id].y -= dy;
        }
        if (!v_fixed) {
            node_displacements_[v_id].x += dx;
            node_displacements_[v_id].y += dy;
        }
    }
}

void GraphLayoutEngine::cool_down() {
    t_ *= C_COOLING;
}

void GraphLayoutEngine::update_positions() {
    for (const auto& node : input_nodes_) {
        if (node.is_fixed) continue;

        int id = node.id;
        double dx = node_displacements_[id].x;
        double dy = node_displacements_[id].y;
        double dist = std::sqrt(dx*dx + dy*dy);

        if (dist > 0) {
            // Apply displacement limited by temperature
            node_positions_[id].x_pos += (dx / dist) * std::min(dist, t_);
            node_positions_[id].y_pos += (dy / dist) * std::min(dist, t_);
            
            // Boundary constraints
            node_positions_[id].x_pos = std::max(-W_/2.0, std::min(W_/2.0, node_positions_[id].x_pos));
            node_positions_[id].y_pos = std::max(-H_/2.0, std::min(H_/2.0, node_positions_[id].y_pos));
        }
    }
}

std::vector<NodeOutput> GraphLayoutEngine::computeLayout(int max_iterations, double initial_temperature) {
    if (input_nodes_.empty()) return {};

    t_ = initial_temperature;

    for (int iter = 0; iter < max_iterations; iter++) {
        apply_repulsive_forces();
        apply_attractive_forces();

        update_positions();
        cool_down();
    }

    std::vector<NodeOutput> final_positions;
    for (const auto& pair : node_positions_) {
        final_positions.push_back(pair.second);
    }
    return final_positions;
}