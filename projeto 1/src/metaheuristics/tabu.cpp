#include "tabu.h"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <limits>
#include <optional>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

#include "../core/route.h"
#include "../heuristics/local_search.h"
#include "../heuristics/vnd.h"
#include "../utils/timer.h"

namespace vrptw {

static bool isBetter(double newCost, std::size_t newRoutes, double oldCost, std::size_t oldRoutes, double eps) {
  if (newCost < oldCost - eps) return true;
  if (std::fabs(newCost - oldCost) <= eps && newRoutes < oldRoutes) return true;
  return false;
}

static bool isTabu(const LSMove& m, const std::vector<int>& tabuUntil, int iter) {
  for (int c : m.customers) {
    if (c <= 0) continue;
    const auto idx = static_cast<std::size_t>(c);
    if (idx < tabuUntil.size() && tabuUntil[idx] > iter) return true;
  }
  return false;
}

static bool isAspired(const LSMove& m, const Solution& best, double eps) {
  return isBetter(m.newCost, m.newRoutes, best.cost, best.numRoutes(), eps);
}

static int sampleTenure(std::mt19937& rng, int tenureMin, int tenureMax) {
  if (tenureMin >= tenureMax) return tenureMin;
  std::uniform_int_distribution<int> dist(tenureMin, tenureMax);
  return dist(rng);
}

Solution tabuSearch(const Instance& inst, Solution start, const TabuParams& params, TabuRunStats* stats,
                    const std::string& convergenceCsvPath) {
  if (stats) *stats = TabuRunStats{};
  if (params.tenureMin <= 0 || params.tenureMax <= 0) {
    throw std::runtime_error("Tabu tenure deve ser >= 1");
  }
  if (params.tenureMin > params.tenureMax) {
    throw std::runtime_error("Tabu tenure invalido: tenure_min > tenure_max");
  }

  std::ofstream conv;
  if (!convergenceCsvPath.empty()) {
    conv.open(convergenceCsvPath);
    conv << "iteration,best_cost,best_routes\n";
  }

  const bool hasTimeLimit = params.timeLimitSec > 0.0;
  const bool hasIterLimit = params.maxIters > 0;
  const bool hasNoImproveLimit = params.maxNoImprove > 0;
  Timer timer;

  Solution cur = std::move(start);
  if (!cur.recompute(inst, params.eps)) {
    throw std::runtime_error("Tabu recebeu solucao inicial infeasible");
  }
  Solution best = cur;

  std::vector<int> tabuUntil(inst.customers.size(), 0);
  std::mt19937 tenureRng(params.rngSeed);

  int noImprove = 0;
  for (int iter = 1;; ++iter) {
    if (hasIterLimit && iter > params.maxIters) break;
    if (hasTimeLimit && timer.elapsedSeconds() >= params.timeLimitSec) break;
    std::optional<LSMove> chosenMove;
    double chosenMoveScore = std::numeric_limits<double>::infinity();
    std::size_t chosenMoveRoutes = cur.numRoutes();
    // Aspiration-by-default fallback: melhor movimento absoluto da iteracao.
    std::optional<LSMove> bestTabuMove;
    double bestTabuScore = std::numeric_limits<double>::infinity();
    std::size_t bestTabuRoutes = cur.numRoutes();

    // Select admissible move based on configured policy.
    auto consider = [&](const LSMove& cand) -> bool {
      if (isBetter(cand.newCost, cand.newRoutes, bestTabuScore, bestTabuRoutes, params.eps)) {
        bestTabuMove = cand;
        bestTabuScore = cand.newCost;
        bestTabuRoutes = cand.newRoutes;
      }

      const bool tabu = isTabu(cand, tabuUntil, iter);
      if (tabu && !isAspired(cand, best, params.eps)) return false;

      if (params.movePolicy == TabuMovePolicy::First) {
        chosenMove = cand;
        return true;  // stop at first admissible move
      }

      if (isBetter(cand.newCost, cand.newRoutes, chosenMoveScore, chosenMoveRoutes, params.eps)) {
        chosenMove = cand;
        chosenMoveScore = cand.newCost;
        chosenMoveRoutes = cand.newRoutes;
      }
      return false;  // best-improvement: evaluate all candidates
    };

    const std::vector<VndNeighborhood>& neighborhoodSet =
        params.neighborhoods.empty() ? selectedNeighborhoodSet() : params.neighborhoods;

    for (const VndNeighborhood n : neighborhoodSet) {
      switch (n) {
        case VndNeighborhood::RelocateIntra:
          enumerateRelocateIntra(cur, inst, params.eps, consider);
          break;
        case VndNeighborhood::SwapIntra:
          enumerateSwapIntra(cur, inst, params.eps, consider);
          break;
        case VndNeighborhood::RelocateInter:
          enumerateRelocateInter(cur, inst, params.eps, consider);
          break;
        case VndNeighborhood::OrOpt:
          enumerateOrOpt(cur, inst, params.eps, consider);
          break;
        case VndNeighborhood::SwapInter:
          enumerateSwapInter(cur, inst, params.eps, consider);
          break;
        case VndNeighborhood::TwoOptIntra:
          enumerateTwoOptIntra(cur, inst, params.eps, consider);
          break;
        case VndNeighborhood::TwoOptInter:
          enumerateTwoOptInter(cur, inst, params.eps, consider);
          break;
        case VndNeighborhood::CrossExchange:
          enumerateCrossExchange(cur, inst, params.eps, consider);
          break;
        case VndNeighborhood::Count:
          break;
      }
      if (params.movePolicy == TabuMovePolicy::First && chosenMove.has_value()) break;
    }

    // Aspiration by default: se nao houver movimento admissivel, aceita o melhor tabu.
    if (!chosenMove) {
      chosenMove = bestTabuMove;
    }
    if (!chosenMove) break;

    if (!applyLSMove(cur, inst, *chosenMove, params.eps)) {
      throw std::runtime_error("Aplicacao de movimento gerou solucao infeasible (bug)");
    }

    const int appliedTenure = sampleTenure(tenureRng, params.tenureMin, params.tenureMax);

    // Marcar clientes envolvidos como tabu.
    for (int c : chosenMove->customers) {
      if (c <= 0) continue;
      tabuUntil[static_cast<std::size_t>(c)] = iter + appliedTenure;
    }

    if (Solution::betterCostThenRoutes(cur, best, params.eps)) {
      best = cur;
      noImprove = 0;
    } else {
      ++noImprove;
    }

    if (conv && (iter % std::max(1, params.logStride) == 0)) {
      conv << iter << "," << best.cost << "," << best.numRoutes() << "\n";
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
