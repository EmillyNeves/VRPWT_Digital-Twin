#pragma once

#include <string>
#include <vector>

#include "route.h"

namespace vrptw {

struct Instance;

struct Solution {
  std::vector<Route> routes;
  double cost = 0.0;

  bool recompute(const Instance& inst, double eps = 1e-9);
  std::size_t numRoutes() const { return routes.size(); }

  static bool betterCostThenRoutes(const Solution& a, const Solution& b, double eps = 1e-6);
};

}  // namespace vrptw

