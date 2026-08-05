#pragma once
#include "vrptw/Instance.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Solution.hpp"
#include "vrptw/Neighborhoods.hpp"
#include "vrptw/Logger.hpp"
#include "vrptw/Timer.hpp"
#include <vector>

namespace vrptw {

struct VndConfig {
    std::vector<Neighborhood> order;            // neighborhood order (empty => default)
    bool                      first_improvement = false;
};

// Default promising order (Relocate is the workhorse; inter-route operators
// carry the heavy lifting, as observed in the report).
std::vector<Neighborhood> default_vnd_order();

// Variable Neighborhood Descent (Hansen & Mladenovic 2001): from `sol`, take
// the best (or first) improving move in neighborhood l; on improvement reset to
// l=0, else advance l; stop at a local optimum over all neighborhoods (or when
// the optional stopping criterion fires). Deterministic given a fixed order.
// `move_counter`, if provided, makes snapshot indices continuous across calls
// (used when GRASP runs VND repeatedly).
Solution vnd_local_search(const Instance& inst, const DistanceMatrix& dm, Solution sol,
                          const VndConfig& cfg, Logger* log = nullptr,
                          StoppingCriterion* stop = nullptr, int* move_counter = nullptr);

} // namespace vrptw
