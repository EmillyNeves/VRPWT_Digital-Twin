#pragma once

#include <vector>

namespace vrptw {

struct Instance;

struct Route {
  std::vector<int> seq;  // includes depot at start/end
  int load = 0;
  double cost = 0.0;

  bool recompute(const Instance& inst, double eps = 1e-9);
  bool isTrivial() const { return seq.size() <= 2; }  // [0,0]
};

}  // namespace vrptw

