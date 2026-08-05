#pragma once

#include <cstddef>
#include <string>
#include <unordered_set>
#include <vector>

#include "customer.h"

namespace vrptw {

struct Instance {
  std::string name;
  int vehicleCount = 0;
  int capacity = 0;
  std::vector<Customer> customers;  // includes depot at index 0

  std::vector<std::vector<double>> dist;
  std::vector<std::vector<int>> nearest;                 // nearest[i] stores ids
  std::vector<std::unordered_set<int>> nearestSet;       // for O(1) membership
  std::size_t kNeighbors = 20;

  static Instance readSolomon(const std::string& path, std::size_t kNeighbors = 20);

  std::size_t size() const { return customers.size(); }
  bool isNeighborOrDepot(int a, int b) const;
};

}  // namespace vrptw

