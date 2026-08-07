#pragma once
#include "vrptw/Instance.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Solution.hpp"
#include <string>
#include <vector>

namespace vrptw {

// Independent re-check of a solution. Does NOT trust Route caches: it re-walks
// every route from scratch. Used (a) on every produced solution and (b) on the
// reference files to confirm the parser/distance computation are correct.
struct ValidationResult {
    bool                     feasible            = true;
    bool                     all_customers_once  = true;
    bool                     capacity_ok         = true;
    bool                     time_ok             = true;
    bool                     returns_to_depot_ok = true;
    double                   distance            = 0.0;  // full precision, recomputed here
    int                      vehicles            = 0;
    std::vector<std::string> errors;
};

ValidationResult validate(const Instance& inst, const DistanceMatrix& dm, const Solution& s);

} // namespace vrptw
