#pragma once
#include "vrptw/Instance.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Solution.hpp"
#include <cmath>

namespace vrptw {

// Solomon lexicographic key: fewer vehicles first, then shorter distance
// (distance rounded to 2 decimals). Lower is better.
struct LexKey {
    int    vehicles = 0;
    double dist2    = 0.0;
    bool operator<(const LexKey& o) const {
        if (vehicles != o.vehicles) return vehicles < o.vehicles;
        return dist2 < o.dist2 - 1e-9;
    }
};

// Single source of truth for "which solution is better". The search optimizes
// the PRIMARY objective (total distance, DIMACS, reported at 1 decimal). The
// lexicographic key is computed for the secondary report only.
class Evaluator {
public:
    Evaluator(const Instance& inst, const DistanceMatrix& dm) : inst_(inst), dm_(dm) {}

    // Total distance in full precision, computed straight from the sequences
    // (independent of Route caches — acts as a cross-check against them).
    double primary(const Solution& s) const {
        double total = 0.0;
        for (const auto& r : s.routes) {
            if (r.empty()) continue;
            int prev = 0;
            for (int c : r.seq) { total += dm_(prev, c); prev = c; }
            total += dm_(prev, 0);
        }
        return total;
    }

    int    vehicles(const Solution& s) const { return s.num_vehicles(); }
    LexKey lex(const Solution& s) const { return LexKey{vehicles(s), round2(primary(s))}; }

    bool better_primary(const Solution& a, const Solution& b) const {
        return primary(a) < primary(b) - 1e-9;
    }
    bool better_lex(const Solution& a, const Solution& b) const {
        return lex(a) < lex(b);
    }

    static double round1(double v) { return std::round(v * 10.0) / 10.0; }
    static double round2(double v) { return std::round(v * 100.0) / 100.0; }

private:
    const Instance&       inst_;
    const DistanceMatrix& dm_;
};

} // namespace vrptw
