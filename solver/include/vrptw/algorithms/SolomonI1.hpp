#pragma once
#include "vrptw/Instance.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Solution.hpp"
#include <vector>

namespace vrptw {

// Solomon's I1 sequential insertion heuristic (1987), p.257:
//
//   c11(i,u,j) = d(i,u) + d(u,j) - mu*d(i,j),        mu >= 0
//   c12(i,u,j) = b_ju - b_j                          (push forward at j)
//   c1 (i,u,j) = alpha1*c11 + alpha2*c12,            alpha1 + alpha2 = 1
//   c2 (i,u,j) = lambda*d(0,u) - c1(i,u,j),          lambda >= 0
//
// Each route is seeded, then customers are inserted one at a time: for every
// unrouted u take the feasible position minimizing c1, then insert the u
// maximizing c2. Deterministic.
//
// Solomon publishes I1 as the BEST OF EIGHT runs (p.259): the four parameter
// sets (mu,lambda,alpha1,alpha2) in {(1,1,1,0), (1,2,1,0), (1,1,0,1), (1,2,0,1)}
// crossed with the two seeding criteria below. He also concludes (p.263) that
// "time insertion proved clearly superior to distance insertion". The DEFAULTS
// here are (1,2,1,0) + farthest, i.e. ONE of those eight -- and the distance
// insertion variant. Do not call it "the canonical configuration".
enum class I1Seed {
    FarthestFromDepot,   // (a) the farthest unrouted customer
    EarliestDeadline     // (b) the unrouted customer with the earliest deadline
};

struct I1Params {
    double mu     = 1.0;
    double lambda = 2.0;
    double alpha1 = 1.0;
    double alpha2 = 0.0;
    I1Seed seed   = I1Seed::FarthestFromDepot;
    // Solomon does not say how to break ties in c1. With alpha1 = 0 the criterion
    // degenerates (c1 == 0 at many positions) and the tie-break dominates the
    // result, so it is exposed as a sensitivity control (S1). false => the first
    // position scanned wins, which is the historical behaviour.
    bool   tie_break_c11 = false;
    // S5: c12 = b_ju - b_j is undefined when u is appended at the END of a route,
    // because the successor is then the depot and has no b_j. Default: use the
    // delay of the return to the depot. true => treat it as zero instead. This
    // matters most where routes are long and few (the type-2 families).
    bool   c12_zero_at_end = false;
    // S3: under the earliest-deadline rule dozens of customers share the same due
    // date in the C families, and Solomon does not say how to break the tie.
    // false => lowest id (the historical behaviour); true => farthest from depot.
    bool   seed_tie_farthest = false;
};

struct I1Candidate {
    int    u   = -1;
    int    pos = -1;
    double c1  = 0.0;
    double c2  = 0.0;
};

// Seed of a new route among the unrouted customers (`routed` is indexed by node
// id; routed[0] is the depot and must be set). Ties are broken by the lowest id
// under both rules -- the article does not specify this (S3), and in the C
// families dozens of customers share the same due date.
int i1_select_seed(const Instance& inst, const DistanceMatrix& dm,
                   const std::vector<char>& routed, I1Seed rule, bool tie_farthest = false);

// Best feasible insertion position of u in r under Solomon's c1, with c2 filled
// in. Returns false when u has no feasible position. This is the SINGLE
// implementation of Solomon's criterion: both solomon_i1() and the GRASP
// randomized construction go through it.
bool i1_best_insertion(const Instance& inst, const DistanceMatrix& dm, const Route& r,
                       int u, const I1Params& p, I1Candidate& out);

// Build a complete feasible solution by sequential insertion. Deterministic.
Solution solomon_i1(const Instance& inst, const DistanceMatrix& dm, const I1Params& p = {});

} // namespace vrptw
