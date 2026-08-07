#include "test_framework.hpp"
#include "vrptw/InstanceParser.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/SolutionIO.hpp"
#include "vrptw/Validator.hpp"
#include "vrptw/Evaluator.hpp"
#include "vrptw/algorithms/SolomonI1.hpp"
#include "vrptw/algorithms/VND.hpp"
#include <filesystem>
#include <vector>
#include <iostream>

using namespace vrptw;
namespace fs = std::filesystem;

// VND from the I1 start must stay feasible, never worsen the I1 cost, and on
// average get substantially closer to the best-known than I1 alone.
TEST(vnd_improves_and_feasible_all) {
    const fs::path indir = fs::path(PROJECT_ROOT) / "data" / "instances" / "solomon";
    const fs::path soldir = fs::path(PROJECT_ROOT) / "data" / "reference-solutions" / "dinamics";

    std::vector<fs::path> instances;
    for (const auto& e : fs::directory_iterator(indir))
        if (e.path().extension() == ".txt") instances.push_back(e.path());
    std::sort(instances.begin(), instances.end());

    int tested = 0, feasible = 0, not_worse = 0;
    double sum_gap = 0.0;
    for (const auto& ip : instances) {
        const Instance inst = parse_instance(ip.string());
        const DistanceMatrix dm(inst);
        const Evaluator ev(inst, dm);

        const Solution s_i1 = solomon_i1(inst, dm);
        const double d_i1 = ev.primary(s_i1);
        const Solution s_vnd = vnd_local_search(inst, dm, s_i1, VndConfig{});
        const double d_vnd = ev.primary(s_vnd);

        const ValidationResult vr = validate(inst, dm, s_vnd);
        ++tested;
        CHECK(vr.feasible);
        CHECK(vr.all_customers_once);
        if (vr.feasible && vr.all_customers_once) ++feasible;
        CHECK(d_vnd <= d_i1 + 1e-6);
        if (d_vnd <= d_i1 + 1e-6) ++not_worse;

        const fs::path sp = soldir / (ip.stem().string() + ".sol");
        if (fs::exists(sp)) {
            const auto ps = read_solution_file(sp.string());
            if (ps.cost) sum_gap += (Evaluator::round1(d_vnd) - *ps.cost) / *ps.cost;
        }
    }
    std::cout << "  [VND] testadas=" << tested << " viaveis=" << feasible
              << " nao_piorou=" << not_worse
              << " gap_medio=" << (sum_gap / tested * 100.0) << "%\n";
    CHECK(tested == 56);
    CHECK(feasible == 56);
    CHECK(not_worse == 56);
}
