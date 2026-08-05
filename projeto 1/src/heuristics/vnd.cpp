#include "vnd.h"

#include "../utils/timer.h"

namespace vrptw {

const std::vector<VndNeighborhood>& selectedNeighborhoodSet() {
  // Selecionado no protocolo de neighborhood selection:
  // {relocate_intra, swap_intra, relocate_inter, two_opt_inter}.
  static const std::vector<VndNeighborhood> kSelected = {
      VndNeighborhood::RelocateIntra,
      VndNeighborhood::SwapIntra,
      VndNeighborhood::RelocateInter,
      VndNeighborhood::TwoOptInter,
  };
  return kSelected;
}

const char* vndNeighborhoodName(VndNeighborhood n) {
  switch (n) {
    case VndNeighborhood::RelocateIntra:
      return "relocate_intra";
    case VndNeighborhood::SwapIntra:
      return "swap_intra";
    case VndNeighborhood::RelocateInter:
      return "relocate_inter";
    case VndNeighborhood::OrOpt:
      return "or_opt";
    case VndNeighborhood::SwapInter:
      return "swap_inter";
    case VndNeighborhood::TwoOptIntra:
      return "two_opt_intra";
    case VndNeighborhood::TwoOptInter:
      return "two_opt_inter";
    case VndNeighborhood::CrossExchange:
      return "cross_exchange";
    case VndNeighborhood::Count:
      return "unknown";
  }
  return "unknown";
}

Solution vnd(const Instance& inst, Solution start, const VndParams& params, VndRunStats* stats) {
  if (!start.recompute(inst, params.ls.eps)) return start;
  if (stats) *stats = VndRunStats{};

  const bool hasTimeLimit = params.timeLimitSec > 0.0;
  Timer timer;

  std::vector<VndNeighborhood> order = params.neighborhoods;
  if (order.empty()) {
    order = selectedNeighborhoodSet();
  }

  std::size_t k = 0;
  while (k < order.size()) {
    if (hasTimeLimit && timer.elapsedSeconds() >= params.timeLimitSec) break;
    const VndNeighborhood nk = order[k];
    const std::size_t idx = static_cast<std::size_t>(nk);
    if (stats) stats->neighborhoods[idx].tries += 1;

    const double beforeCost = start.cost;
    const std::size_t beforeRoutes = start.numRoutes();
    bool improved = false;

    switch (nk) {
      case VndNeighborhood::RelocateIntra:
        improved = relocateIntraFirst(start, inst, params.ls);
        break;
      case VndNeighborhood::SwapIntra:
        improved = swapIntraFirst(start, inst, params.ls);
        break;
      case VndNeighborhood::RelocateInter:
        improved = relocateInterFirst(start, inst, params.ls);
        break;
      case VndNeighborhood::OrOpt:
        improved = orOptFirst(start, inst, params.ls);
        break;
      case VndNeighborhood::SwapInter:
        improved = swapInterFirst(start, inst, params.ls);
        break;
      case VndNeighborhood::TwoOptIntra:
        improved = twoOptIntraFirst(start, inst, params.ls);
        break;
      case VndNeighborhood::TwoOptInter:
        improved = twoOptInterFirst(start, inst, params.ls);
        break;
      case VndNeighborhood::CrossExchange:
        improved = crossExchangeFirst(start, inst, params.ls);
        break;
      default:
        break;
    }

    if (improved) {
      if (stats) {
        VndNeighborhoodStats& st = stats->neighborhoods[idx];
        st.applied += 1;
        st.totalCostDelta += (beforeCost - start.cost);
        st.totalRoutesDelta += static_cast<int>(beforeRoutes) - static_cast<int>(start.numRoutes());
      }
      k = 0;
    } else {
      ++k;
    }
  }
  return start;
}

}  // namespace vrptw
