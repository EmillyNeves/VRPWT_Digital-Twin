#pragma once

#include "../core/instance.h"
#include "../core/solution.h"

namespace vrptw {

struct I1Params {
  double mu = 1.0;
  // Classical Solomon-I1 setting for distance-oriented baseline.
  double lambdaCoef = 1.0;
  // Solomon I1: c1 = alpha1 * c11 + alpha2 * c12, with alpha1 + alpha2 = 1.
  double alpha1 = 1.0;
  double alpha2 = 0.0;
  double eps = 1e-6;
};

Solution solomonI1(const Instance& inst, const I1Params& params);

}  // namespace vrptw
