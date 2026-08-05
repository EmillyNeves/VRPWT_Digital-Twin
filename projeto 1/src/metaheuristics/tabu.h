#pragma once

#include <string>
#include <vector>

#include "../core/instance.h"
#include "../core/solution.h"
#include "../heuristics/vnd.h"

namespace vrptw {

enum class TabuMovePolicy { Best, First };

struct TabuParams {
  TabuMovePolicy movePolicy = TabuMovePolicy::Best;
  int tenureMin = 15;
  int tenureMax = 15;
  unsigned int rngSeed = 42;
  int maxIters = 10000;      // 0 = sem limite
  int maxNoImprove = 500;    // 0 = sem limite
  double eps = 1e-6;
  int logStride = 1;
  double timeLimitSec = 0.0;  // 0 = sem limite de tempo
  // Conjunto de vizinhancas para exploracao tabu (vazio = selecionado padrao).
  std::vector<VndNeighborhood> neighborhoods;
};

struct TabuRunStats {
  int itersDone = 0;
  int noImprove = 0;
};

Solution tabuSearch(const Instance& inst, Solution start, const TabuParams& params, TabuRunStats* stats,
                    const std::string& convergenceCsvPath = "");

}  // namespace vrptw
