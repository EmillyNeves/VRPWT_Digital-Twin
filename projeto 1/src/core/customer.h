#pragma once

namespace vrptw {

struct Customer {
  int id = -1;
  double x = 0.0;
  double y = 0.0;
  int demand = 0;
  double ready = 0.0;
  double due = 0.0;
  double service = 0.0;
};

}  // namespace vrptw

