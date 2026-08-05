#include "vrptw/algorithms/VND.hpp"
#include "vrptw/Evaluator.hpp"

namespace vrptw {

std::vector<Neighborhood> default_vnd_order() {
    return {Neighborhood::Relocate, Neighborhood::OrOpt, Neighborhood::Swap,
            Neighborhood::TwoOpt, Neighborhood::CrossExchange};
}

Solution vnd_local_search(const Instance& inst, const DistanceMatrix& dm, Solution sol,
                          const VndConfig& cfg, Logger* log,
                          StoppingCriterion* stop, int* move_counter) {
    const std::vector<Neighborhood> order = cfg.order.empty() ? default_vnd_order() : cfg.order;
    const Evaluator ev(inst, dm);
    sol.recompute_all(inst, dm);

    int local_idx = 0;
    int& midx = move_counter ? *move_counter : local_idx;

    std::size_t l = 0;
    while (l < order.size()) {
        if (stop && stop->should_stop()) break;
        const Move m = find_best_move(sol, inst, dm, order[l], cfg.first_improvement);
        if (m.type != MoveType::None && m.delta < -1e-7) {
            apply_move(sol, m, inst, dm);
            ++midx;
            if (log) {
                const double cost = ev.primary(sol);
                const long ms = stop ? stop->elapsed_ms() : 0;
                log->on_improve(ms, cost);
                log->on_move(midx, ms, cost, sol, move_name(m.type));
            }
            l = 0;                 // back to the first neighborhood
        } else {
            ++l;                   // try the next neighborhood
        }
    }
    sol.prune_empty();
    return sol;
}

} // namespace vrptw
