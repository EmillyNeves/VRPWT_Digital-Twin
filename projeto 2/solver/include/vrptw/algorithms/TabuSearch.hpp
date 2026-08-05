#pragma once
#include "vrptw/Instance.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Solution.hpp"
#include "vrptw/Timer.hpp"
#include "vrptw/Logger.hpp"

namespace vrptw {

// Classic Tabu Search (Glover 1989/1990), simplest textbook form. Each
// iteration moves to the best admissible neighbor over the shared kit (accepting
// non-improving moves to escape local optima). A move is tabu if a customer it
// touches was moved within the last `tenure` iterations, unless it aspirates
// (yields a new global best). Returns the best solution found. Deterministic.
struct TabuConfig {
    int    tenure         = 15;
    int    max_iters      = -1;   // hard cap on total iterations (-1 => disabled)
    int    max_no_improve = -1;   // PRIMARY stop: iterations without improving the best (-1 => disabled).
                                  // One iteration = one neighbourhood move.
    double target         = -1.0; // stop when best <= target (<0 => disabled); for TTT
};

// `out_iters`, if given, receives the number of Tabu iterations actually run
// (one iteration = one neighbourhood move), for transparency.
Solution tabu_search(const Instance& inst, const DistanceMatrix& dm, Solution start,
                     StoppingCriterion& stop, const TabuConfig& cfg, Logger* log = nullptr,
                     long* out_iters = nullptr);

} // namespace vrptw
