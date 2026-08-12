#include "vrptw/algorithms/SolomonI1.hpp"
#include "vrptw/Neighborhoods.hpp"   // eval_insert
#include <cmath>
#include <limits>
#include <vector>

namespace vrptw {

namespace {
constexpr double kInf = std::numeric_limits<double>::max();
}

int i1_select_seed(const Instance& inst, const DistanceMatrix& dm,
                   const std::vector<char>& routed, I1Seed rule, bool tie_farthest) {
    const int n = static_cast<int>(inst.size());
    int seed = -1;
    if (rule == I1Seed::FarthestFromDepot) {
        double best = -1.0;
        for (int u = 1; u < n; ++u)
            if (!routed[static_cast<std::size_t>(u)] && dm(0, u) > best) { best = dm(0, u); seed = u; }
    } else {
        double best = kInf;
        for (int u = 1; u < n; ++u) {
            if (routed[static_cast<std::size_t>(u)]) continue;
            const double due = inst.node(u).due;
            if (due < best) { best = due; seed = u; }
            // S3: due dates are integers in the Solomon instances, so ties are exact
            else if (tie_farthest && seed >= 0 && due == best && dm(0, u) > dm(0, seed)) seed = u;
        }
    }
    return seed;
}

bool i1_best_insertion(const Instance& inst, const DistanceMatrix& dm, const Route& r,
                       int u, const I1Params& p, I1Candidate& out) {
    const int m = static_cast<int>(r.len());
    double best_c1 = kInf, best_c11 = kInf;
    int    pos_u = -1;

    for (int pos = 0; pos <= m; ++pos) {
        const InsertEval ie = eval_insert(inst, dm, r, pos, u);
        if (!ie.feasible) continue;
        const int pred = (pos == 0) ? 0 : r.seq[static_cast<std::size_t>(pos) - 1];
        const int succ = (pos == m) ? 0 : r.seq[static_cast<std::size_t>(pos)];

        // c11 written in the article's own form. With mu == 1 this is bit-identical
        // to ie.ddist (= d(i,u)+d(u,j)-d(i,j)); the frozen baseline test proves it.
        const double c11 = dm(pred, u) + dm(u, succ) - p.mu * dm(pred, succ);
        const double c12 = (p.c12_zero_at_end && pos == m) ? 0.0 : ie.dtime;   // S5
        const double c1  = p.alpha1 * c11 + p.alpha2 * c12;

        bool better = c1 < best_c1;
        if (!better && p.tie_break_c11 && pos_u >= 0 &&
            std::fabs(c1 - best_c1) <= 1e-9 && c11 < best_c11 - 1e-9) {
            better = true;                                          // S1: tie broken by c11
        }
        if (better) { best_c1 = c1; best_c11 = c11; pos_u = pos; }
    }

    if (pos_u < 0) return false;
    out.u   = u;
    out.pos = pos_u;
    out.c1  = best_c1;
    out.c2  = p.lambda * dm(0, u) - best_c1;
    return true;
}

Solution solomon_i1(const Instance& inst, const DistanceMatrix& dm, const I1Params& p) {
    const int n = static_cast<int>(inst.size());

    Solution sol;
    std::vector<char> routed(static_cast<std::size_t>(n), 0);
    routed[0] = 1;
    int remaining = inst.num_customers();

    while (remaining > 0) {
        const int seed = i1_select_seed(inst, dm, routed, p.seed, p.seed_tie_farthest);
        if (seed < 0) break;                       // defensive: nothing left to seed with

        Route r;
        r.seq = {seed};
        r.recompute(inst, dm);
        routed[static_cast<std::size_t>(seed)] = 1;
        --remaining;

        // greedily insert the customer maximizing c2 until none fits, then close
        while (true) {
            int    best_u = -1, best_pos = -1;
            double best_c2 = -kInf;
            I1Candidate cand;
            for (int u = 1; u < n; ++u) {
                if (routed[static_cast<std::size_t>(u)]) continue;
                if (!i1_best_insertion(inst, dm, r, u, p, cand)) continue;
                if (cand.c2 > best_c2) { best_c2 = cand.c2; best_u = cand.u; best_pos = cand.pos; }
            }
            if (best_u < 0) break;
            r.seq.insert(r.seq.begin() + best_pos, best_u);
            r.recompute(inst, dm);
            routed[static_cast<std::size_t>(best_u)] = 1;
            --remaining;
        }

        sol.routes.push_back(std::move(r));
    }

    return sol;
}

} // namespace vrptw
