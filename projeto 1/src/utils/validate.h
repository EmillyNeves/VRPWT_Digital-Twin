#pragma once

#include <string>

namespace vrptw {

struct Instance;
struct Solution;

// Validates structural constraints, customer coverage, feasibility (capacity + time windows),
// and recomputes route loads/costs.
bool validateSolution(Solution& sol, const Instance& inst, double eps, std::string* error);

}  // namespace vrptw

