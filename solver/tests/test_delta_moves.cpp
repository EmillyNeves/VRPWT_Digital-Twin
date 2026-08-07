#include "test_framework.hpp"
#include "vrptw/InstanceParser.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Solution.hpp"
#include "vrptw/Neighborhoods.hpp"
#include "vrptw/Evaluator.hpp"
#include "vrptw/Validator.hpp"
#include <filesystem>
#include <iostream>
#include <string>

using namespace vrptw;
namespace fs = std::filesystem;

// Feasible but poor start: one customer per route. Far from optimal, so every
// neighborhood has plenty of improving moves to exercise.
static Solution one_per_route(const Instance& inst, const DistanceMatrix& dm) {
    Solution s;
    for (int c = 1; c < static_cast<int>(inst.size()); ++c) {
        Route r;
        r.seq = {c};
        r.recompute(inst, dm);
        s.routes.push_back(std::move(r));
    }
    return s;
}

static void descend_and_check(const std::string& inst_name) {
    const Instance inst = parse_instance((fs::path(PROJECT_ROOT) / "data" / "instances" / "solomon" / (inst_name + ".txt")).string());
    const DistanceMatrix dm(inst);
    const Evaluator ev(inst, dm);

    Solution sol = one_per_route(inst, dm);
    const double start_dist = ev.primary(sol);

    const Neighborhood order[] = {Neighborhood::Relocate, Neighborhood::OrOpt,
                                  Neighborhood::Swap, Neighborhood::TwoOpt,
                                  Neighborhood::CrossExchange};
    int applied = 0, c_reloc = 0, c_or = 0, c_swap = 0, c_2opt = 0, c_cross = 0;
    bool improved = true;
    int guard = 0;
    while (improved && guard++ < 100000) {
        improved = false;
        for (Neighborhood nb : order) {
            const Move m = find_best_move(sol, inst, dm, nb, /*first_improvement=*/false);
            if (m.type == MoveType::None) continue;

            const double before = ev.primary(sol);
            const double predicted = before + m.delta;
            apply_move(sol, m, inst, dm);
            const double after = ev.primary(sol);

            CHECK(m.delta < 0.0);                       // only improving moves accepted
            CHECK_NEAR(after, predicted, 1e-6);         // delta path == apply/recompute path
            const ValidationResult vr = validate(inst, dm, sol);
            CHECK(vr.all_customers_once);               // coverage preserved
            CHECK(vr.feasible);                         // feasible move => feasible solution
            CHECK_NEAR(vr.distance, after, 1e-6);       // validator distance == evaluator distance

            switch (m.type) {
                case MoveType::Relocate:      ++c_reloc; break;
                case MoveType::OrOpt:         ++c_or;    break;
                case MoveType::Swap:          ++c_swap;  break;
                case MoveType::TwoOpt:        ++c_2opt;  break;
                case MoveType::CrossExchange: ++c_cross; break;
                default: break;
            }
            ++applied;
            improved = true;
        }
    }

    const double final_dist = ev.primary(sol);
    std::cout << "  [" << inst_name << "] inicio=" << start_dist
              << " final=" << final_dist << " movs=" << applied
              << " (reloc=" << c_reloc << " oropt=" << c_or << " swap=" << c_swap
              << " 2opt=" << c_2opt << " cross=" << c_cross << ")\n";

    CHECK(applied > 0);
    CHECK(final_dist < start_dist);
    CHECK(c_reloc > 0);          // the workhorse operator must have fired
    const ValidationResult fv = validate(inst, dm, sol);
    CHECK(fv.feasible);
    CHECK(fv.all_customers_once);
}

TEST(delta_matches_apply_C101) { descend_and_check("C101"); }
TEST(delta_matches_apply_R101) { descend_and_check("R101"); }
TEST(delta_matches_apply_RC101) { descend_and_check("RC101"); }
