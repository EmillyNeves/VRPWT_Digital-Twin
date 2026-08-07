#pragma once
#include "vrptw/Instance.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Route.hpp"
#include <vector>

namespace vrptw {

// A complete VRPTW solution: a set of routes. Empty routes are allowed
// transiently but the vehicle count counts only non-empty routes.
struct Solution {
    std::vector<Route> routes;

    void recompute_all(const Instance& inst, const DistanceMatrix& dm) {
        for (auto& r : routes) r.recompute(inst, dm);
    }

    double total_distance() const {
        double d = 0.0;
        for (const auto& r : routes) d += r.distance;
        return d;
    }

    int num_vehicles() const {
        int v = 0;
        for (const auto& r : routes) if (!r.empty()) ++v;
        return v;
    }

    bool feasible() const {
        for (const auto& r : routes) if (!r.empty() && !r.feasible) return false;
        return true;
    }

    // Drop empty routes (a vehicle is freed when an inter-route move empties it).
    void prune_empty() {
        std::vector<Route> kept;
        kept.reserve(routes.size());
        for (auto& r : routes) if (!r.empty()) kept.push_back(std::move(r));
        routes.swap(kept);
    }
};

} // namespace vrptw
