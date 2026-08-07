#include "test_framework.hpp"
#include "vrptw/InstanceParser.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/SolutionIO.hpp"
#include "vrptw/Validator.hpp"
#include "vrptw/Evaluator.hpp"
#include "vrptw/algorithms/SolomonI1.hpp"
#include <filesystem>
#include <vector>
#include <iostream>

using namespace vrptw;
namespace fs = std::filesystem;

// Solomon I1 must always produce a COMPLETE, FEASIBLE solution for every
// instance, and (being a heuristic) a cost no better than the best-known.
TEST(i1_feasible_on_all_instances) {
    const fs::path indir = fs::path(PROJECT_ROOT) / "data" / "instances" / "solomon";
    const fs::path soldir = fs::path(PROJECT_ROOT) / "data" / "reference-solutions" / "dinamics";

    std::vector<fs::path> instances;
    for (const auto& e : fs::directory_iterator(indir))
        if (e.path().extension() == ".txt") instances.push_back(e.path());
    std::sort(instances.begin(), instances.end());

    int tested = 0, feasible = 0, ge_bestknown = 0;
    double sum_gap = 0.0;
    for (const auto& ip : instances) {
        const Instance inst = parse_instance(ip.string());
        const DistanceMatrix dm(inst);
        const Evaluator ev(inst, dm);
        const Solution sol = solomon_i1(inst, dm);
        const ValidationResult vr = validate(inst, dm, sol);
        ++tested;
        CHECK(vr.feasible);
        CHECK(vr.all_customers_once);
        if (vr.feasible && vr.all_customers_once) ++feasible;

        const double ours = Evaluator::round1(ev.primary(sol));
        const fs::path sp = soldir / (ip.stem().string() + ".sol");
        if (fs::exists(sp)) {
            const auto ps = read_solution_file(sp.string());
            if (ps.cost) {
                if (ours >= *ps.cost - 0.05) ++ge_bestknown;     // heuristic >= best-known
                sum_gap += (ours - *ps.cost) / *ps.cost;
            }
        }
    }
    std::cout << "  [I1] testadas=" << tested << " viaveis=" << feasible
              << " >=bestknown=" << ge_bestknown
              << " gap_medio=" << (sum_gap / tested * 100.0) << "%\n";
    CHECK(tested == 56);
    CHECK(feasible == 56);
    CHECK(ge_bestknown == 56);
}
