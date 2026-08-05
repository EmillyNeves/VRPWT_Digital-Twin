#pragma once
#include "vrptw/Instance.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Solution.hpp"

namespace vrptw {

// Parameters of Solomon's I1 sequential insertion heuristic (1987).
// Fixed canonical configuration for this study (NOT tuned by irace), so the
// initial solution is identical and deterministic for every metaheuristic.
//   c1 = a1*(d(i,u)+d(u,j) - mu*d(i,j)) + a2*(b_ju - b_j)
//   c2 = lambda*d(0,u) - c1   (selects the customer that maximizes c2)
// With a2 = 0 the time-delay term is omitted (time windows still constrain
// feasibility); seed of each new route = farthest unrouted customer from depot.
struct I1Params {
    double mu     = 1.0;
    double lambda = 2.0;
    double alpha1 = 1.0;
    double alpha2 = 0.0;   // fixed at 0 in this study
};

// Build a complete feasible solution by sequential insertion. Deterministic.
Solution solomon_i1(const Instance& inst, const DistanceMatrix& dm, const I1Params& p = {});

} // namespace vrptw
