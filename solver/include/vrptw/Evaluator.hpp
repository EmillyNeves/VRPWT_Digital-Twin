#pragma once
#include "vrptw/Instance.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Solution.hpp"
#include "vrptw/Validator.hpp"
#include <cmath>

namespace vrptw {

// Solomon's lexicographic ordering, verbatim from the paper (1987, p.259):
// "Solution quality is measured in terms of the minimum number of vehicles,
//  minimum schedule time, minimum distance, and minimum waiting time in that
//  order, i.e., we use a lexicographic ordering of the solutions."
// Lower is better. Continuous keys are rounded to 2 decimals (the SINTEF/Solomon
// reporting convention) before comparison.
//
// NOTE: this is NOT the objective the search optimizes. The search minimizes
// total distance only (the 12th DIMACS convention, `primary()` below). This key
// exists to reproduce Solomon's own "best of eight runs" selection when checking
// our I1 against his Tables I-VI. Do not mix the two.
struct LexKey {
    int    vehicles = 0;
    double sched2   = 0.0;
    double dist2    = 0.0;
    double wait2    = 0.0;
    bool operator<(const LexKey& o) const {
        if (vehicles != o.vehicles)               return vehicles < o.vehicles;
        if (std::fabs(sched2 - o.sched2) > 1e-9)  return sched2 < o.sched2;
        if (std::fabs(dist2  - o.dist2)  > 1e-9)  return dist2  < o.dist2;
        return wait2 < o.wait2 - 1e-9;
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

    int vehicles(const Solution& s) const { return s.num_vehicles(); }

    // Solomon's 4-level key needs schedule and waiting time, which only the
    // Validator produces (a Solution alone does not carry them).
    static LexKey lex(const ValidationResult& v) {
        return LexKey{v.vehicles, round2(v.schedule_time),
                      round2(v.distance), round2(v.waiting_time)};
    }
    static bool better_lex(const ValidationResult& a, const ValidationResult& b) {
        return lex(a) < lex(b);
    }

    bool better_primary(const Solution& a, const Solution& b) const {
        return primary(a) < primary(b) - 1e-9;
    }

    static double round1(double v) { return std::round(v * 10.0) / 10.0; }
    static double round2(double v) { return std::round(v * 100.0) / 100.0; }

private:
    const Instance&       inst_;
    const DistanceMatrix& dm_;
};

} // namespace vrptw
