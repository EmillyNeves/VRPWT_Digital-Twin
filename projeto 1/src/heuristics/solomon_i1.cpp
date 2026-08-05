#include "solomon_i1.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <vector>

namespace vrptw {

static int selectSeedFarthest(const Instance& inst, const std::vector<int>& unrouted) {
  int bestId = -1;
  double bestD = -1.0;
  for (int u : unrouted) {
    const double d = inst.dist[0][static_cast<std::size_t>(u)];
    if (d > bestD) {
      bestD = d;
      bestId = u;
    }
  }
  return bestId;
}

struct BestInsertion {
  int customer = -1;
  std::size_t pos = 0;  // insert before pos (between pos-1 and pos)
  double c1 = std::numeric_limits<double>::infinity();
  double c2 = -std::numeric_limits<double>::infinity();
};

struct RouteTiming {
  std::vector<double> begin;     // service start at each position in route
  std::vector<double> depart;    // service end at each position in route
  std::vector<double> fwdSlack;  // max delay absorbable from this position onward
};

static bool computeRouteTiming(const Route& r, const Instance& inst, double eps, RouteTiming& timing) {
  timing.begin.assign(r.seq.size(), 0.0);
  timing.depart.assign(r.seq.size(), 0.0);
  timing.fwdSlack.assign(r.seq.size(), 0.0);
  if (r.seq.size() < 2) return false;
  if (r.seq.front() != 0 || r.seq.back() != 0) return false;

  int load = 0;
  double t = 0.0;
  timing.depart[0] = 0.0;
  for (std::size_t idx = 0; idx + 1 < r.seq.size(); ++idx) {
    const int i = r.seq[idx];
    const int j = r.seq[idx + 1];
    const auto& cust = inst.customers[static_cast<std::size_t>(j)];

    const double arrival = t + inst.dist[static_cast<std::size_t>(i)][static_cast<std::size_t>(j)];
    const double start = std::max(arrival, cust.ready);
    if (start > cust.due + eps) return false;
    timing.begin[idx + 1] = start;
    t = start + cust.service;
    timing.depart[idx + 1] = t;

    if (j != 0) load += cust.demand;
    if (load > inst.capacity) return false;
  }

  // Forward slack (time-warp style): largest additional delay at position idx
  // that still keeps all downstream due times feasible.
  const std::size_t last = r.seq.size() - 1;
  const int lastNode = r.seq[last];
  timing.fwdSlack[last] = inst.customers[static_cast<std::size_t>(lastNode)].due + eps - timing.begin[last];
  for (std::size_t rev = last; rev-- > 0;) {
    const int i = r.seq[rev];
    const int j = r.seq[rev + 1];
    const double directArrivalAtJ = timing.depart[rev] + inst.dist[static_cast<std::size_t>(i)][static_cast<std::size_t>(j)];
    const double waitAtJ = std::max(0.0, timing.begin[rev + 1] - directArrivalAtJ);
    const double localSlack = inst.customers[static_cast<std::size_t>(i)].due + eps - timing.begin[rev];
    timing.fwdSlack[rev] = std::min(localSlack, waitAtJ + timing.fwdSlack[rev + 1]);
  }
  return true;
}

static bool tryBestInsertionInRoute(const Instance& inst, const I1Params& params, const std::vector<int>& unrouted,
                                    const Route& baseRoute, BestInsertion& best) {
  best = BestInsertion{};

  RouteTiming timing;
  if (!computeRouteTiming(baseRoute, inst, params.eps, timing)) {
    throw std::runtime_error("Rota base infeasible em I1 (bug)");
  }

  for (int u : unrouted) {
    if (baseRoute.load + inst.customers[static_cast<std::size_t>(u)].demand > inst.capacity) continue;

    BestInsertion bestForU;
    bestForU.customer = u;

    for (std::size_t k = 1; k < baseRoute.seq.size(); ++k) {
      const int i = baseRoute.seq[k - 1];
      const int j = baseRoute.seq[k];
      const auto& cu = inst.customers[static_cast<std::size_t>(u)];
      const auto& cj = inst.customers[static_cast<std::size_t>(j)];

      const double arrivalU = timing.depart[k - 1] + inst.dist[static_cast<std::size_t>(i)][static_cast<std::size_t>(u)];
      const double startU = std::max(arrivalU, cu.ready);
      if (startU > cu.due + params.eps) continue;
      const double departU = startU + cu.service;

      const double arrivalJNew = departU + inst.dist[static_cast<std::size_t>(u)][static_cast<std::size_t>(j)];
      const double startJNew = std::max(arrivalJNew, cj.ready);
      const double c12 = startJNew - timing.begin[k];
      if (c12 > timing.fwdSlack[k] + params.eps) continue;

      const double c11 = inst.dist[static_cast<std::size_t>(i)][static_cast<std::size_t>(u)] +
                         inst.dist[static_cast<std::size_t>(u)][static_cast<std::size_t>(j)] -
                         params.mu * inst.dist[static_cast<std::size_t>(i)][static_cast<std::size_t>(j)];

      // Solomon I1 classical insertion criterion:
      // c1 = alpha1 * c11 + alpha2 * c12, with c12 = b_j(new) - b_j(old).
      const double c1 = params.alpha1 * c11 + params.alpha2 * c12;
      if (c1 >= bestForU.c1 - params.eps) continue;

      bestForU.pos = k;
      bestForU.c1 = c1;
    }

    if (bestForU.customer == -1 || !std::isfinite(bestForU.c1)) continue;

    // Solomon-I1 selection stage: choose customer by highest c2 after each customer's best c1 insertion.
    bestForU.c2 = params.lambdaCoef * inst.dist[0][static_cast<std::size_t>(u)] - bestForU.c1;

    if (best.customer == -1) {
      best = bestForU;
      continue;
    }

    if (bestForU.c2 > best.c2 + params.eps ||
        (std::fabs(bestForU.c2 - best.c2) <= params.eps && bestForU.c1 < best.c1 - params.eps)) {
      best = bestForU;
    }
  }

  return best.customer != -1;
}

Solution solomonI1(const Instance& inst, const I1Params& params) {
  if (inst.customers.size() < 2) throw std::runtime_error("Instancia sem clientes");
  if (params.alpha1 < 0.0 || params.alpha2 < 0.0) {
    throw std::runtime_error("I1 classico exige alpha1, alpha2 >= 0");
  }
  if (std::fabs((params.alpha1 + params.alpha2) - 1.0) > params.eps) {
    throw std::runtime_error("I1 classico exige alpha1 + alpha2 = 1");
  }

  std::vector<int> unrouted;
  unrouted.reserve(inst.customers.size() - 1);
  for (std::size_t i = 1; i < inst.customers.size(); ++i) unrouted.push_back(static_cast<int>(i));

  Solution sol;
  sol.routes.clear();

  while (!unrouted.empty()) {
    if (static_cast<int>(sol.routes.size()) >= inst.vehicleCount) break;

    const int seed = selectSeedFarthest(inst, unrouted);
    if (seed < 0) break;

    Route r;
    r.seq = {0, seed, 0};
    if (!r.recompute(inst, params.eps)) throw std::runtime_error("Seed infeasible: " + std::to_string(seed));
    unrouted.erase(std::remove(unrouted.begin(), unrouted.end(), seed), unrouted.end());

    // Classical sequential I1: saturate the current route before opening the next one.
    while (!unrouted.empty()) {
      BestInsertion best;
      if (!tryBestInsertionInRoute(inst, params, unrouted, r, best)) break;

      r.seq.insert(r.seq.begin() + static_cast<std::ptrdiff_t>(best.pos), best.customer);
      if (!r.recompute(inst, params.eps)) throw std::runtime_error("Insercao gerou rota invalida (bug)");
      unrouted.erase(std::remove(unrouted.begin(), unrouted.end(), best.customer), unrouted.end());
    }

    sol.routes.push_back(std::move(r));
  }

  if (!unrouted.empty()) {
    throw std::runtime_error("I1 nao construiu solucao completa: clientes nao atendidos=" +
                             std::to_string(unrouted.size()) + ", limite de veiculos=" +
                             std::to_string(inst.vehicleCount));
  }

  if (!sol.recompute(inst, params.eps)) throw std::runtime_error("Solucao final infeasible (bug)");
  if (static_cast<int>(sol.routes.size()) > inst.vehicleCount) throw std::runtime_error("Excedeu numero de veiculos");
  return sol;
}

}  // namespace vrptw
