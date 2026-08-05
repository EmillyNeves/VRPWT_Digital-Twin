#include "grasp.h"

#include <algorithm>
#include <cstddef>
#include <cmath>
#include <fstream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

#include "../heuristics/solomon_i1.h"
#include "../heuristics/vnd.h"
#include "../utils/timer.h"

namespace vrptw {

struct InsertionCandidate {
  int customer = -1;
  std::size_t routeIdx = 0;
  std::size_t pos = 0;
  double c1 = 0.0;
};

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

static bool coversAllCustomers(const Solution& sol, const Instance& inst) {
  if (static_cast<int>(sol.routes.size()) > inst.vehicleCount) return false;

  const std::size_t n = inst.customers.size();
  std::vector<int> seen(n, 0);

  for (const Route& r : sol.routes) {
    if (r.seq.size() < 2) return false;
    if (r.seq.front() != 0 || r.seq.back() != 0) return false;
    for (std::size_t i = 1; i + 1 < r.seq.size(); ++i) {
      const int c = r.seq[i];
      if (c <= 0 || static_cast<std::size_t>(c) >= n) return false;
      if (++seen[static_cast<std::size_t>(c)] > 1) return false;
    }
  }

  for (std::size_t c = 1; c < n; ++c) {
    if (seen[c] != 1) return false;
  }
  return true;
}

static double clampAlpha(double alpha, double eps) {
  if (alpha < -eps || alpha > 1.0 + eps) {
    throw std::runtime_error("alpha fora de [0,1]: " + std::to_string(alpha));
  }
  return std::clamp(alpha, 0.0, 1.0);
}

static std::vector<double> normalizeReactiveAlphas(const std::vector<double>& in, double eps) {
  std::vector<double> out;
  out.reserve(in.size());
  for (double alpha : in) out.push_back(clampAlpha(alpha, eps));
  std::sort(out.begin(), out.end());
  out.erase(std::unique(out.begin(), out.end(), [eps](double a, double b) { return std::fabs(a - b) <= eps; }), out.end());
  return out;
}

static void resetReactiveBlockStats(std::vector<int>& count, std::vector<double>& sumCost) {
  std::fill(count.begin(), count.end(), 0);
  std::fill(sumCost.begin(), sumCost.end(), 0.0);
}

static void updateReactiveProbabilities(const Solution& best, const std::vector<int>& blockCount,
                                        const std::vector<double>& blockCost, std::vector<double>& probabilities,
                                        double gamma, double eps) {
  std::vector<double> quality(probabilities.size(), 0.0);
  const double base = std::max(best.cost, eps);
  const double gammaSafe = std::max(0.0, gamma);

  for (std::size_t i = 0; i < probabilities.size(); ++i) {
    if (blockCount[i] <= 0) continue;
    const double avg = blockCost[i] / static_cast<double>(blockCount[i]);
    if (avg <= eps) continue;
    quality[i] = std::pow(base / avg, gammaSafe);
  }

  const double qsum = std::accumulate(quality.begin(), quality.end(), 0.0);
  if (qsum <= eps) {
    const double uniform = 1.0 / static_cast<double>(probabilities.size());
    std::fill(probabilities.begin(), probabilities.end(), uniform);
    return;
  }
  for (std::size_t i = 0; i < probabilities.size(); ++i) probabilities[i] = quality[i] / qsum;
}

static Solution constructGrasp(const Instance& inst, std::mt19937& rng, const GraspParams& p) {
  std::vector<int> unrouted;
  unrouted.reserve(inst.customers.size() - 1);
  for (std::size_t i = 1; i < inst.customers.size(); ++i) unrouted.push_back(static_cast<int>(i));

  Solution sol;
  sol.routes.clear();

  while (!unrouted.empty()) {
    if (static_cast<int>(sol.routes.size()) >= inst.vehicleCount) break;

    // Start with a farthest seed (deterministic).
    const int seed = selectSeedFarthest(inst, unrouted);
    if (seed < 0) break;
    Route r;
    r.seq = {0, seed, 0};
    if (!r.recompute(inst, p.eps)) throw std::runtime_error("Seed infeasible: " + std::to_string(seed));
    sol.routes.push_back(std::move(r));
    unrouted.erase(std::remove(unrouted.begin(), unrouted.end(), seed), unrouted.end());

    while (!unrouted.empty()) {
      std::vector<InsertionCandidate> cand;
      cand.reserve(unrouted.size() * 4);

      double cmin = std::numeric_limits<double>::infinity();
      double cmax = -std::numeric_limits<double>::infinity();

      for (int u : unrouted) {
        const int demand = inst.customers[static_cast<std::size_t>(u)].demand;
        for (std::size_t rIdx = 0; rIdx < sol.routes.size(); ++rIdx) {
          const Route& base = sol.routes[rIdx];
          if (base.load + demand > inst.capacity) continue;
          for (std::size_t k = 1; k < base.seq.size(); ++k) {
            const int i = base.seq[k - 1];
            const int j = base.seq[k];
            const double c1 = inst.dist[static_cast<std::size_t>(i)][static_cast<std::size_t>(u)] +
                              inst.dist[static_cast<std::size_t>(u)][static_cast<std::size_t>(j)] -
                              p.mu * inst.dist[static_cast<std::size_t>(i)][static_cast<std::size_t>(j)];

            Route test = base;
            test.seq.insert(test.seq.begin() + static_cast<std::ptrdiff_t>(k), u);
            if (!test.recompute(inst, p.eps)) continue;

            cand.push_back(InsertionCandidate{.customer = u, .routeIdx = rIdx, .pos = k, .c1 = c1});
            cmin = std::min(cmin, c1);
            cmax = std::max(cmax, c1);
          }
        }
      }

      if (cand.empty()) break;

      const double limit = cmin + p.alpha * (cmax - cmin);
      std::vector<std::size_t> rcl;
      rcl.reserve(cand.size());
      for (std::size_t idx = 0; idx < cand.size(); ++idx) {
        if (cand[idx].c1 <= limit + p.eps) rcl.push_back(idx);
      }
      if (rcl.empty()) break;

      std::uniform_int_distribution<std::size_t> distIdx(0, rcl.size() - 1);
      const InsertionCandidate chosen = cand[rcl[distIdx(rng)]];

      Route& target = sol.routes[chosen.routeIdx];
      target.seq.insert(target.seq.begin() + static_cast<std::ptrdiff_t>(chosen.pos), chosen.customer);
      if (!target.recompute(inst, p.eps)) throw std::runtime_error("Insercao infeasible apos selecao (bug)");
      unrouted.erase(std::remove(unrouted.begin(), unrouted.end(), chosen.customer), unrouted.end());
    }
  }

  if (!unrouted.empty()) {
    throw std::runtime_error("GRASP construtivo nao gerou solucao completa: clientes nao atendidos=" +
                             std::to_string(unrouted.size()) + ", limite de veiculos=" +
                             std::to_string(inst.vehicleCount));
  }

  sol.recompute(inst, p.eps);
  return sol;
}

Solution grasp(const Instance& inst, std::mt19937& rng, const GraspParams& params, GraspRunStats* stats,
               const std::string& convergenceCsvPath) {
  if (stats) *stats = GraspRunStats{};

  const GraspMode mode = params.mode;
  const int reactiveUpdate = std::max(1, params.reactiveUpdate);
  const double fixedAlpha = clampAlpha(params.alpha, params.eps);

  std::vector<double> reactiveAlphas;
  std::vector<double> reactiveProb;
  std::vector<int> reactiveCount;
  std::vector<double> reactiveCost;
  if (mode == GraspMode::Reactive) {
    reactiveAlphas = normalizeReactiveAlphas(params.reactiveAlphas, params.eps);
    if (reactiveAlphas.empty()) {
      throw std::runtime_error("GRASP reativo exige --reactive-alphas com ao menos 1 valor em [0,1]");
    }
    reactiveProb.assign(reactiveAlphas.size(), 1.0 / static_cast<double>(reactiveAlphas.size()));
    reactiveCount.assign(reactiveAlphas.size(), 0);
    reactiveCost.assign(reactiveAlphas.size(), 0.0);
  }

  std::ofstream conv;
  if (!convergenceCsvPath.empty()) {
    conv.open(convergenceCsvPath);
    conv << "iteration,best_cost,best_routes,alpha_used\n";
  }

  const bool hasTimeLimit = params.timeLimitSec > 0.0;
  const bool hasIterLimit = params.maxIters > 0;
  const bool hasNoImproveLimit = params.maxNoImprove > 0;
  Timer timer;

  // Use pure I1 as the initial incumbent; GRASP iterations handle local search via VND.
  Solution best = solomonI1(inst, I1Params{.mu = params.mu, .eps = params.eps});
  if (!best.recompute(inst, params.eps) || !coversAllCustomers(best, inst)) {
    throw std::runtime_error("Incumbente inicial (I1) ficou infeasible (bug)");
  }

  int noImprove = 0;
  for (int iter = 1;; ++iter) {
    if (hasIterLimit && iter > params.maxIters) break;
    if (hasTimeLimit && timer.elapsedSeconds() >= params.timeLimitSec) break;
    double alphaUsed = fixedAlpha;
    std::size_t alphaIdx = 0;
    if (mode == GraspMode::Reactive) {
      std::discrete_distribution<std::size_t> distAlpha(reactiveProb.begin(), reactiveProb.end());
      alphaIdx = distAlpha(rng);
      alphaUsed = reactiveAlphas[alphaIdx];
    }

    GraspParams iterParams = params;
    iterParams.mode = GraspMode::Fixed;
    iterParams.alpha = alphaUsed;

    Solution s = constructGrasp(inst, rng, iterParams);
    if (!coversAllCustomers(s, inst)) {
      if (mode == GraspMode::Reactive) {
        reactiveCount[alphaIdx] += 1;
        reactiveCost[alphaIdx] += best.cost * 1.25;
      }
      ++noImprove;
      if (conv && (iter % std::max(1, params.logStride) == 0)) {
        conv << iter << "," << best.cost << "," << best.numRoutes() << "," << alphaUsed << "\n";
      }
      if (mode == GraspMode::Reactive && (iter % reactiveUpdate == 0)) {
        updateReactiveProbabilities(best, reactiveCount, reactiveCost, reactiveProb, params.reactiveGamma, params.eps);
        resetReactiveBlockStats(reactiveCount, reactiveCost);
      }
      if (stats) {
        stats->itersDone = iter;
        stats->noImprove = noImprove;
      }
      if (hasNoImproveLimit && noImprove >= params.maxNoImprove) break;
      continue;
    }
    double remainingTime = 0.0;
    if (hasTimeLimit) {
      remainingTime = std::max(0.0, params.timeLimitSec - timer.elapsedSeconds());
      if (remainingTime <= 0.0) break;
    }

    s = vnd(inst, std::move(s),
            VndParams{
                .ls = LocalSearchParams{.eps = params.eps},
                .timeLimitSec = hasTimeLimit ? remainingTime : 0.0,
                .neighborhoods = params.neighborhoods,
            });
    if (!coversAllCustomers(s, inst)) {
      if (mode == GraspMode::Reactive) {
        reactiveCount[alphaIdx] += 1;
        reactiveCost[alphaIdx] += best.cost * 1.25;
      }
      ++noImprove;
      if (conv && (iter % std::max(1, params.logStride) == 0)) {
        conv << iter << "," << best.cost << "," << best.numRoutes() << "," << alphaUsed << "\n";
      }
      if (mode == GraspMode::Reactive && (iter % reactiveUpdate == 0)) {
        updateReactiveProbabilities(best, reactiveCount, reactiveCost, reactiveProb, params.reactiveGamma, params.eps);
        resetReactiveBlockStats(reactiveCount, reactiveCost);
      }
      if (stats) {
        stats->itersDone = iter;
        stats->noImprove = noImprove;
      }
      if (hasNoImproveLimit && noImprove >= params.maxNoImprove) break;
      continue;
    }

    if (mode == GraspMode::Reactive) {
      reactiveCount[alphaIdx] += 1;
      reactiveCost[alphaIdx] += s.cost;
    }

    if (Solution::betterCostThenRoutes(s, best, params.eps)) {
      best = std::move(s);
      noImprove = 0;
    } else {
      ++noImprove;
    }

    if (conv && (iter % std::max(1, params.logStride) == 0)) {
      conv << iter << "," << best.cost << "," << best.numRoutes() << "," << alphaUsed << "\n";
    }

    if (mode == GraspMode::Reactive && (iter % reactiveUpdate == 0)) {
      updateReactiveProbabilities(best, reactiveCount, reactiveCost, reactiveProb, params.reactiveGamma, params.eps);
      resetReactiveBlockStats(reactiveCount, reactiveCost);
    }

    if (hasNoImproveLimit && noImprove >= params.maxNoImprove) {
      if (stats) {
        stats->itersDone = iter;
        stats->noImprove = noImprove;
      }
      break;
    }
    if (stats) {
      stats->itersDone = iter;
      stats->noImprove = noImprove;
    }
  }

  best.recompute(inst, params.eps);
  return best;
}

}  // namespace vrptw
