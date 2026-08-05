#pragma once
#include "vrptw/Instance.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Solution.hpp"
#include <string>
#include <vector>
#include <optional>

namespace vrptw {

// Raw routes parsed from a reference solution file. `cost` is present for the
// Dinamics ".sol" dialect (final "Cost <d>" line) and absent for the SINTEF
// dialect (which omits the cost). Both dialects use "Route ... : c1 c2 ...".
struct ParsedSolution {
    std::vector<std::vector<int>> routes;
    std::optional<double>         cost;
};

ParsedSolution read_solution_file(const std::string& path);

// Build a Solution (with recomputed caches) from parsed routes.
Solution to_solution(const ParsedSolution& ps, const Instance& inst, const DistanceMatrix& dm);

// Write a solution in the Dinamics-style ".sol" format (routes + Cost@1dp).
void write_solution(const std::string& path, const Solution& s);

} // namespace vrptw
