#pragma once
#include "vrptw/Instance.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Solution.hpp"
#include "vrptw/Rng.hpp"
#include "vrptw/Timer.hpp"
#include "vrptw/Logger.hpp"
#include "vrptw/algorithms/VND.hpp"
#include "vrptw/algorithms/SolomonI1.hpp"
#include <vector>

namespace vrptw {

// Classic GRASP (Feo & Resende 1995): repeat { greedy-randomized construction;
// local search } and keep the best. Construction = Solomon I1 with a value-based
// Restricted Candidate List controlled by alpha (alpha=0 greedy, alpha=1 random).
// Reactive variant (Prais & Ribeiro 2000): a discrete set of alpha values with
// probabilities updated from the average quality each alpha produced. Kept to
// the simplest textbook form; only alpha (and, for reactive, the alpha set /
// delta / block) are parameters.
struct GraspConfig {
    double                alpha = 0.3;            // fixed GRASP RCL parameter
    bool                  reactive = false;
    std::vector<double>   alpha_set;              // reactive: discrete alphas (empty => default grid)
    double                delta = 1.0;            // reactive: probability-update exponent
    int                   block = 50;             // reactive: iterations between probability updates
    VndConfig             vnd;                    // local search
    I1Params              i1;                     // Solomon criterion used by the construction
    int                   max_iters = -1;         // hard cap on total iterations (-1 => disabled)
    int                   max_no_improve = -1;    // PRIMARY stop: iterations without improving the best
                                                  // (-1 => disabled). One iteration = one construction+VND.
    double                target = -1.0;          // stop when best <= target (<0 => disabled); for TTT
};

// Greedy-randomized construction (one route at a time). Deterministic greedy
// when alpha==0. Used internally by grasp() and reusable on its own.
Solution grasp_construct(const Instance& inst, const DistanceMatrix& dm, Rng& rng,
                         double alpha, const I1Params& p = {});

// `out_iters`, if given, receives the number of GRASP iterations actually run
// (one iteration = one greedy-randomized construction + VND), for transparency.
Solution grasp(const Instance& inst, const DistanceMatrix& dm, StoppingCriterion& stop,
               Rng& rng, const GraspConfig& cfg, Logger* log = nullptr, int* out_iters = nullptr);

} // namespace vrptw
