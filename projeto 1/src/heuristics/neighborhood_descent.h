#pragma once

#include "../core/instance.h"
#include "../core/solution.h"
#include "vnd.h"

namespace vrptw {

struct NeighborhoodDescentParams {
  VndParams base;
  bool restartOnImprove = false;  // false = passes sem reinicio estilo VND
};

Solution neighborhoodDescent(const Instance& inst, Solution start, const NeighborhoodDescentParams& params,
                             VndRunStats* stats = nullptr);

}  // namespace vrptw

