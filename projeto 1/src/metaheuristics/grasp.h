#pragma once

#include <random>
#include <string>
#include <vector>

#include "../core/instance.h"
#include "../core/solution.h"
#include "../heuristics/vnd.h"

namespace vrptw {

enum class GraspMode { Fixed, Reactive };

struct GraspParams {
  GraspMode mode = GraspMode::Fixed;
  double alpha = 0.3;
  std::vector<double> reactiveAlphas = {0.1, 0.2, 0.3, 0.4, 0.5};
  int reactiveUpdate = 25;
  double reactiveGamma = 1.0;
  double mu = 1.0;
  int maxIters = 10000;      // 0 = sem limite
  int maxNoImprove = 500;    // 0 = sem limite
  double eps = 1e-6;
  int logStride = 1;
  double timeLimitSec = 0.0;  // 0 = sem limite de tempo
  // Conjunto de vizinhancas para o VND interno (vazio = selecionado padrao).
  std::vector<VndNeighborhood> neighborhoods;
};

struct GraspRunStats {
  int itersDone = 0;
  int noImprove = 0;
};

Solution grasp(const Instance& inst, std::mt19937& rng, const GraspParams& params, GraspRunStats* stats,
               const std::string& convergenceCsvPath = "");

}  // namespace vrptw
