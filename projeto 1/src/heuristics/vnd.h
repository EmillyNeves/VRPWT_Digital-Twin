#pragma once

#include <array>
#include <cstddef>
#include <vector>

#include "../core/instance.h"
#include "../core/solution.h"
#include "local_search.h"

namespace vrptw {

enum class VndNeighborhood : std::size_t {
  RelocateIntra = 0,
  SwapIntra = 1,
  RelocateInter = 2,
  OrOpt = 3,
  SwapInter = 4,
  TwoOptIntra = 5,
  TwoOptInter = 6,   // two_opt_star_inter
  CrossExchange = 7,
  Count = 8
};

constexpr std::size_t kVndNeighborhoodCount = static_cast<std::size_t>(VndNeighborhood::Count);

struct VndNeighborhoodStats {
  int tries = 0;
  int applied = 0;
  double totalCostDelta = 0.0;
  int totalRoutesDelta = 0;
};

struct VndRunStats {
  std::array<VndNeighborhoodStats, kVndNeighborhoodCount> neighborhoods{};
};

struct VndParams {
  LocalSearchParams ls;
  double timeLimitSec = 0.0;  // 0 = sem limite de tempo
  // Vazio = conjunto selecionado padrao (definido por selecao de vizinhancas).
  std::vector<VndNeighborhood> neighborhoods;
};

// Conjunto padrao selecionado para uso em VND/NLS/GRASP/Tabu.
// Ordem respeita complexidade crescente.
const std::vector<VndNeighborhood>& selectedNeighborhoodSet();

const char* vndNeighborhoodName(VndNeighborhood n);
Solution vnd(const Instance& inst, Solution start, const VndParams& params, VndRunStats* stats = nullptr);

}  // namespace vrptw
