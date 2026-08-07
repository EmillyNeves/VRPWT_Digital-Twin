#include "test_framework.hpp"
#include "vrptw/InstanceParser.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/SolutionIO.hpp"
#include "vrptw/Validator.hpp"
#include "vrptw/Evaluator.hpp"
#include <filesystem>
#include <vector>
#include <string>
#include <iostream>
#include <cmath>

using namespace vrptw;
namespace fs = std::filesystem;

// THE headline gate (M2): for every Solomon instance, feed the Dinamics
// reference routes into our pipeline and require that (a) the routes are
// feasible and (b) our distance @1dp reproduces the file's Cost (+/- 0.05).
// A failure here means the distance/rounding convention is wrong.
TEST(reproduce_dinamics_costs) {
    const fs::path root(PROJECT_ROOT);
    const fs::path indir = root / "data" / "instances" / "solomon";
    const fs::path soldir = root / "data" / "reference-solutions" / "dinamics";

    std::vector<fs::path> instances;
    for (const auto& e : fs::directory_iterator(indir))
        if (e.path().extension() == ".txt") instances.push_back(e.path());
    std::sort(instances.begin(), instances.end());

    int tested = 0, feasible = 0, matched = 0;
    for (const auto& ip : instances) {
        const fs::path sp = soldir / (ip.stem().string() + ".sol");
        if (!fs::exists(sp)) continue;

        const Instance inst = parse_instance(ip.string());
        const DistanceMatrix dm(inst);
        const ParsedSolution ps = read_solution_file(sp.string());
        const Solution sol = to_solution(ps, inst, dm);
        const ValidationResult vr = validate(inst, dm, sol);
        ++tested;

        CHECK(vr.feasible);
        if (vr.feasible) ++feasible;

        if (ps.cost) {
            const double ours = Evaluator::round1(vr.distance);
            CHECK_NEAR(ours, *ps.cost, 0.05);
            if (std::fabs(ours - *ps.cost) <= 0.05) ++matched;
            else std::cerr << "    -> " << ip.stem().string()
                           << ": nosso=" << ours << " arquivo=" << *ps.cost << "\n";
        }
    }

    std::cout << "  [refs] testadas=" << tested
              << " viaveis=" << feasible
              << " custos_batem=" << matched << "\n";
    CHECK(tested == 56);
    CHECK(feasible == tested);
    CHECK(matched == tested);
}
