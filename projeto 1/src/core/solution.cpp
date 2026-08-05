#include "solution.h"

#include <algorithm>

#include "instance.h"

namespace vrptw {

bool Solution::recompute(const Instance& inst, double eps) {
  cost = 0.0;

  // Remove trivial routes.
  routes.erase(std::remove_if(routes.begin(), routes.end(), [](const Route& r) { return r.isTrivial(); }), routes.end());

  for (auto& r : routes) {
    if (!r.recompute(inst, eps)) return false;
    cost += r.cost;
  }
  return true;
}

bool Solution::betterCostThenRoutes(const Solution& a, const Solution& b, double eps) {
  if (a.cost < b.cost - eps) return true;
  if (b.cost < a.cost - eps) return false;
  return a.routes.size() < b.routes.size();
}

}  // namespace vrptw

