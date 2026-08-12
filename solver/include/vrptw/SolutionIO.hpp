#pragma once
#include "vrptw/Instance.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Solution.hpp"
#include <string>
#include <vector>
#include <optional>

namespace vrptw {

// Raw routes parsed from a reference solution file. `cost` is present for the
// CVRPLIB/DIMACS ".sol" dialect (final "Cost <d>" line, truncated convention)
// and absent for the SINTEF dialect. Both use "Route ... : c1 c2 ...".
//
// `reference` is a quirk of the SINTEF files: seven of them (r112, r203, r207,
// r211, rc107, rc202, rc203) carry a FULL-PRECISION cost in the "Reference"
// header field instead of a bibliographic citation, e.g.
//     Reference     : 1049.6242367397954
// Those values are the double-precision Euclidean cost of the routes below, and
// they are the only exact anchor available for the --dist-mode double path.
// The other 49 files hold prose there and leave this field empty.
struct ParsedSolution {
    std::vector<std::vector<int>> routes;
    std::optional<double>         cost;
    std::optional<double>         reference;
};

ParsedSolution read_solution_file(const std::string& path);

// Build a Solution (with recomputed caches) from parsed routes.
Solution to_solution(const ParsedSolution& ps, const Instance& inst, const DistanceMatrix& dm);

// Write a solution in the Dinamics-style ".sol" format (routes + Cost@1dp).
void write_solution(const std::string& path, const Solution& s);

} // namespace vrptw
