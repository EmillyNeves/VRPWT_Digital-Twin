#include "test_framework.hpp"
#include "vrptw/InstanceParser.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/SolutionIO.hpp"
#include "vrptw/Validator.hpp"
#include "vrptw/Evaluator.hpp"
#include "vrptw/Rng.hpp"
#include "vrptw/algorithms/SolomonI1.hpp"
#include "vrptw/algorithms/VND.hpp"
#include "vrptw/algorithms/Grasp.hpp"
#include <filesystem>
#include <iostream>
#include <string>

using namespace vrptw;
namespace fs = std::filesystem;

// GRASP (fixed or reactive) over several iterations must stay feasible and be
// no worse than a single VND from I1 (it keeps the best of many starts).
// Deterministic here via a fixed seed + fixed iteration count.
static void run_grasp(const std::string& name, bool reactive) {
    const Instance inst = parse_instance((fs::path(PROJECT_ROOT) / "input" / (name + ".txt")).string());
    const DistanceMatrix dm(inst);
    const Evaluator ev(inst, dm);

    const Solution s_i1 = solomon_i1(inst, dm);
    const double d_vnd = ev.primary(vnd_local_search(inst, dm, s_i1, VndConfig{}));

    StoppingCriterion stop(600000);                 // large; iteration count is the binding stop
    Rng rng(make_seed(12345, name, 0));
    GraspConfig cfg;
    cfg.reactive = reactive;
    cfg.alpha = 0.3;
    cfg.max_iters = 60;
    const Solution g = grasp(inst, dm, stop, rng, cfg);
    const double d_g = ev.primary(g);

    const ValidationResult vr = validate(inst, dm, g);
    CHECK(vr.feasible);
    CHECK(vr.all_customers_once);
    CHECK(d_g <= d_vnd + 1e-6);                      // GRASP >= quality of single VND

    const fs::path sp = fs::path(PROJECT_ROOT) / "solution (Dinamics)" / (name + ".sol");
    double gap = -1.0;
    if (fs::exists(sp)) {
        const auto ps = read_solution_file(sp.string());
        if (ps.cost) gap = (Evaluator::round1(d_g) - *ps.cost) / *ps.cost * 100.0;
    }
    std::cout << "  [" << (reactive ? "rGRASP " : "GRASP  ") << name << "] vnd=" << d_vnd
              << " grasp=" << Evaluator::round1(d_g) << " gap=" << gap << "%\n";
}

TEST(grasp_fixed_C101)  { run_grasp("C101", false); }
TEST(grasp_fixed_R101)  { run_grasp("R101", false); }
TEST(grasp_reactive_RC101) { run_grasp("RC101", true); }
