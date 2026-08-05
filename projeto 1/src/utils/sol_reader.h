#pragma once

#include <string>

namespace vrptw {

struct Solution;

// Reads a DIMACS/Solomon ".sol" file produced by writeSol():
//   Route #k: <customers...>
//   Cost <value>
// The cost value is ignored; cost is recomputed by validateSolution().
bool readSol(const std::string& path, Solution* out, std::string* error);

}  // namespace vrptw

