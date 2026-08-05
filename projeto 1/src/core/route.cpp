#include "route.h"

#include <algorithm>
#include <cmath>

#include "instance.h"

namespace vrptw {

bool Route::recompute(const Instance& inst, double eps) {
  load = 0;
  cost = 0.0;
  double t = 0.0;
  if (seq.size() < 2) return false;
  if (seq.front() != 0 || seq.back() != 0) return false;

  for (std::size_t idx = 0; idx + 1 < seq.size(); ++idx) {
    const int i = seq[idx];
    const int j = seq[idx + 1];
    cost += inst.dist[static_cast<std::size_t>(i)][static_cast<std::size_t>(j)];

    const double arrival = t + inst.dist[static_cast<std::size_t>(i)][static_cast<std::size_t>(j)];
    const auto& cust = inst.customers[static_cast<std::size_t>(j)];
    const double start = std::max(arrival, cust.ready);
    if (start > cust.due + eps) return false;
    t = start + cust.service;

    if (j != 0) load += cust.demand;
    if (load > inst.capacity) return false;
  }

  // Limpa lixo de precisão IEEE 754 acumulado na soma de doubles.
  cost = std::round(cost * 10.0) / 10.0;

  return true;
}

}  // namespace vrptw

