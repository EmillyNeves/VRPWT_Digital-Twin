#include "neighborhood_descent.h"

#include <vector>

#include "../utils/timer.h"

namespace vrptw {

static bool applyNeighborhoodFirst(Solution& sol, const Instance& inst, VndNeighborhood n, const LocalSearchParams& ls) {
  switch (n) {
    case VndNeighborhood::RelocateIntra:
      return relocateIntraFirst(sol, inst, ls);
    case VndNeighborhood::SwapIntra:
      return swapIntraFirst(sol, inst, ls);
    case VndNeighborhood::RelocateInter:
      return relocateInterFirst(sol, inst, ls);
    case VndNeighborhood::OrOpt:
      return orOptFirst(sol, inst, ls);
    case VndNeighborhood::SwapInter:
      return swapInterFirst(sol, inst, ls);
    case VndNeighborhood::TwoOptIntra:
      return twoOptIntraFirst(sol, inst, ls);
    case VndNeighborhood::TwoOptInter:
      return twoOptInterFirst(sol, inst, ls);
    case VndNeighborhood::CrossExchange:
      return crossExchangeFirst(sol, inst, ls);
    case VndNeighborhood::Count:
      return false;
  }
  return false;
}

Solution neighborhoodDescent(const Instance& inst, Solution start, const NeighborhoodDescentParams& params,
                             VndRunStats* stats) {
  if (!start.recompute(inst, params.base.ls.eps)) return start;
  if (stats) *stats = VndRunStats{};

  std::vector<VndNeighborhood> order = params.base.neighborhoods;
  if (order.empty()) {
    order = selectedNeighborhoodSet();
  }

  const bool hasTimeLimit = params.base.timeLimitSec > 0.0;
  Timer timer;

  bool improvedAny = true;
  while (improvedAny) {
    improvedAny = false;
    for (VndNeighborhood n : order) {
      if (hasTimeLimit && timer.elapsedSeconds() >= params.base.timeLimitSec) return start;
      const std::size_t idx = static_cast<std::size_t>(n);
      if (stats) stats->neighborhoods[idx].tries += 1;

      const double beforeCost = start.cost;
      const std::size_t beforeRoutes = start.numRoutes();
      const bool improved = applyNeighborhoodFirst(start, inst, n, params.base.ls);
      if (!improved) continue;

      improvedAny = true;
      if (stats) {
        VndNeighborhoodStats& st = stats->neighborhoods[idx];
        st.applied += 1;
        st.totalCostDelta += (beforeCost - start.cost);
        st.totalRoutesDelta += static_cast<int>(beforeRoutes) - static_cast<int>(start.numRoutes());
      }

      if (params.restartOnImprove) break;
    }
  }

  return start;
}

}  // namespace vrptw
