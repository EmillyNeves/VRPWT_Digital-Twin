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
// The four quantities Solomon (1987, p.259) reports are `vehicles`,
// `schedule_time`, `distance` and `waiting_time` -- in that lexicographic order.
// They satisfy, by construction,
//     schedule_time == distance + waiting_time + service_time
// (with travel time == distance, the Solomon convention), and service_time is a
// constant per instance. Only two of the four are therefore independent.
struct ValidationResult {
    bool                     feasible            = true;
    bool                     all_customers_once  = true;
    bool                     capacity_ok         = true;
    bool                     time_ok             = true;
    bool                     returns_to_depot_ok = true;
    double                   distance            = 0.0;  // full precision, recomputed here
    double                   schedule_time       = 0.0;  // sum over routes of (return - departure)
    double                   waiting_time        = 0.0;  // idle time waiting for windows to open
    double                   service_time        = 0.0;  // sum of service times (constant per instance)
    int                      vehicles            = 0;
    std::vector<std::string> errors;
};

ValidationResult validate(const Instance& inst, const DistanceMatrix& dm, const Solution& s);

} // namespace vrptw
