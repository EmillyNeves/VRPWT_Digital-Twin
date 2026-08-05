#pragma once
#include "vrptw/Instance.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Solution.hpp"
#include <vector>
#include <functional>

namespace vrptw {

// The standardized neighborhood kit shared by VND, GRASP and Tabu (the same
// operators for every algorithm = fairness). Intra variants have r1 == r2.
enum class MoveType {
    None,
    Relocate,      // move 1 customer (intra or inter)
    Swap,          // exchange 2 customers (intra or inter)
    TwoOpt,        // reverse a segment within one route (intra)
    OrOpt,         // move a chain of length seg (2..3), intra or inter
    CrossExchange  // exchange a segment of r1 with a segment of r2 (inter)
};

inline const char* move_name(MoveType t) {
    switch (t) {
        case MoveType::Relocate:      return "Relocate";
        case MoveType::Swap:          return "Swap";
        case MoveType::TwoOpt:        return "TwoOpt";
        case MoveType::OrOpt:         return "OrOpt";
        case MoveType::CrossExchange: return "CrossExchange";
        default:                      return "None";
    }
}

struct Move {
    MoveType type = MoveType::None;
    int  r1 = -1, i1 = -1;   // source route / index
    int  r2 = -1, i2 = -1;   // target route / index
    int  seg = 1;            // chain/segment length (OrOpt, CrossExchange)
    int  seg2 = 1;           // second segment length (CrossExchange)
    bool rev = false;        // insert the moved chain reversed (OrOpt)
    bool feasible = false;
    double delta = 0.0;      // change in total distance (negative = improving)
};

// Scalar forward simulation of a single route sequence (no allocation, no
// caches). Travel time == truncated distance. Returns feasibility + distance
// + load. This is the shared, validated evaluation used by every operator.
struct SeqEval { bool feasible = true; double distance = 0.0; double load = 0.0; };
SeqEval evaluate_seq(const Instance& inst, const DistanceMatrix& dm, const std::vector<int>& seq);

// O(1) feasibility + distance delta for inserting customer u at position pos
// (between seq[pos-1] and seq[pos]) of route r, using r's caches (push-forward
// slack). Requires r.recompute() to have been called. Used by Solomon I1 and
// the GRASP randomized construction.
struct InsertEval { bool feasible = false; double ddist = 0.0; };
InsertEval eval_insert(const Instance& inst, const DistanceMatrix& dm,
                       const Route& r, int pos, int u);

// Identifiers for the neighborhoods used by VND's variable ordering.
enum class Neighborhood { Relocate, Swap, TwoOpt, OrOpt, CrossExchange };

// Find the best improving feasible move in the given neighborhood (or, if
// first_improvement, the first one). Returns a Move with type==None if none.
// `sol` must have up-to-date route caches (recompute_all) before calling.
Move find_best_move(const Solution& sol, const Instance& inst, const DistanceMatrix& dm,
                    Neighborhood nb, bool first_improvement);

// Apply a move: mutate the affected route sequences, recompute their caches.
// Does not prune empty routes (call Solution::prune_empty() at safe points).
void apply_move(Solution& sol, const Move& mv, const Instance& inst, const DistanceMatrix& dm);

// Admissibility filter used by Tabu Search. With allow_nonimproving the scan
// keeps the best (lowest-delta) feasible move even if non-improving. A move
// whose attribute is tabu is rejected unless it satisfies aspiration (the
// resulting cost beats the global best).
struct MoveFilter {
    bool                          allow_nonimproving = false;
    std::function<bool(const Move&)> is_tabu;            // null => nothing is tabu
    double                        cur_cost  = 0.0;
    double                        best_cost = 0.0;
};

// Best admissible move over ALL neighborhoods (used by Tabu). Returns
// Move{None} if no admissible move exists.
Move find_best_admissible(const Solution& sol, const Instance& inst,
                          const DistanceMatrix& dm, const MoveFilter& filter);

} // namespace vrptw
