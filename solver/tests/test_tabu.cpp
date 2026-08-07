#include "test_framework.hpp"
#include "vrptw/InstanceParser.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/SolutionIO.hpp"
#include "vrptw/Validator.hpp"
#include "vrptw/Evaluator.hpp"
#include "vrptw/algorithms/SolomonI1.hpp"
#include "vrptw/algorithms/VND.hpp"
#include "vrptw/algorithms/TabuSearch.hpp"
#include <filesystem>
#include <iostream>
#include <string>

using namespace vrptw;
namespace fs = std::filesystem;

// Tabu Search from the I1 start must stay feasible and never end up worse than
// I1 (it returns the best incumbent). Deterministic (no RNG). Fixed iteration
// count for a reproducible test.
static void run_tabu(const std::string& name) {
    const Instance inst = parse_instance((fs::path(PROJECT_ROOT) / "data" / "instances" / "solomon" / (name + ".txt")).string());
    const DistanceMatrix dm(inst);
    const Evaluator ev(inst, dm);

    const Solution s_i1 = solomon_i1(inst, dm);
    const double d_i1  = ev.primary(s_i1);
    const double d_vnd = ev.primary(vnd_local_search(inst, dm, s_i1, VndConfig{}));

    StoppingCriterion stop(600000);
    TabuConfig cfg;
    cfg.tenure = 15;
    cfg.max_iters = 300;
    const Solution t = tabu_search(inst, dm, s_i1, stop, cfg);
    const double d_t = ev.primary(t);

    const ValidationResult vr = validate(inst, dm, t);
    CHECK(vr.feasible);
    CHECK(vr.all_customers_once);
    CHECK(d_t <= d_i1 + 1e-6);

    const fs::path sp = fs::path(PROJECT_ROOT) / "data" / "reference-solutions" / "dinamics" / (name + ".sol");
    double gap = -1.0;
    if (fs::exists(sp)) {
        const auto ps = read_solution_file(sp.string());
        if (ps.cost) gap = (Evaluator::round1(d_t) - *ps.cost) / *ps.cost * 100.0;
    }
    std::cout << "  [Tabu " << name << "] i1=" << d_i1 << " vnd=" << d_vnd
              << " tabu=" << Evaluator::round1(d_t) << " gap=" << gap << "%\n";
}

TEST(tabu_C101)  { run_tabu("C101"); }
TEST(tabu_R101)  { run_tabu("R101"); }
TEST(tabu_RC101) { run_tabu("RC101"); }
