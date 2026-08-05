#include "vrptw/algorithms/TabuSearch.hpp"
#include "vrptw/Neighborhoods.hpp"
#include "vrptw/Evaluator.hpp"
#include <vector>

namespace vrptw {

namespace {
// The customers a move touches (its tabu attribute). 1-2 ids, read from the
// solution BEFORE the move is applied.
void involved(const Solution& s, const Move& m, int out[2], int& k) {
    k = 0;
    switch (m.type) {
        case MoveType::Relocate:
        case MoveType::OrOpt:
            out[k++] = s.routes[m.r1].seq[m.i1];
            break;
        case MoveType::Swap:
        case MoveType::CrossExchange:
            out[k++] = s.routes[m.r1].seq[m.i1];
            out[k++] = s.routes[m.r2].seq[m.i2];
            break;
        case MoveType::TwoOpt:
            out[k++] = s.routes[m.r1].seq[m.i1];
            if (m.i2 < static_cast<int>(s.routes[m.r1].seq.size()))
                out[k++] = s.routes[m.r1].seq[m.i2];
            break;
        default: break;
    }
}
} // namespace

Solution tabu_search(const Instance& inst, const DistanceMatrix& dm, Solution start,
                     StoppingCriterion& stop, const TabuConfig& cfg, Logger* log, long* out_iters) {
    const Evaluator ev(inst, dm);
    Solution sol = std::move(start);
    sol.recompute_all(inst, dm);

    double cur = ev.primary(sol);
    Solution best = sol;
    double best_cost = cur;

    std::vector<long> tabu_until(inst.size(), -1);
    long iter = 0;
    long no_improve = 0;   // consecutive moves without improving the best
    int  snap_idx = 0;

    while (!stop.should_stop()) {                       // time budget acts only as a safety cap
        if (cfg.max_iters >= 0 && iter >= cfg.max_iters) break;

        MoveFilter filt;
        filt.allow_nonimproving = true;
        filt.cur_cost = cur;
        filt.best_cost = best_cost;
        filt.is_tabu = [&](const Move& m) {
            int ids[2], k;
            involved(sol, m, ids, k);
            for (int t = 0; t < k; ++t)
                if (tabu_until[static_cast<std::size_t>(ids[t])] > iter) return true;
            return false;
        };

        const Move m = find_best_admissible(sol, inst, dm, filt);
        if (m.type == MoveType::None) break;   // no admissible move

        int ids[2], k;
        involved(sol, m, ids, k);
        apply_move(sol, m, inst, dm);
        for (int t = 0; t < k; ++t)
            tabu_until[static_cast<std::size_t>(ids[t])] = iter + cfg.tenure;

        cur = ev.primary(sol);
        if (cur < best_cost - 1e-9) {
            best_cost = cur;
            best = sol;
            no_improve = 0;                                                   // best improved: reset
            if (log) {
                const long ms = stop.elapsed_ms();
                log->on_improve(ms, cur);
                log->on_move(++snap_idx, ms, cur, best, "incumbent");
            }
            if (cfg.target >= 0.0 && best_cost <= cfg.target + 1e-6) break;   // target reached (TTT)
        } else {
            ++no_improve;
        }
        ++iter;

        // PRIMARY stopping criterion: K iterations without improvement.
        if (cfg.max_no_improve >= 0 && no_improve >= cfg.max_no_improve) break;
    }

    if (out_iters) *out_iters = iter;
    best.recompute_all(inst, dm);
    return best;
}

} // namespace vrptw
