#include "bks.h"

#include <fstream>
#include <sstream>
#include <string>

namespace vrptw {

std::optional<double> readBksCost(const std::string& path) {
  std::ifstream in(path);
  if (!in) return std::nullopt;

  std::string line;
  while (std::getline(in, line)) {
    if (line.rfind("Cost", 0) == 0) {
      std::istringstream iss(line);
      std::string label;
      double cost = 0.0;
      if (iss >> label >> cost) return cost;
    }
  }
  return std::nullopt;
}

}  // namespace vrptw

