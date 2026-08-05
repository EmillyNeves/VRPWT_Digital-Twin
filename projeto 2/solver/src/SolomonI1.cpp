#include "vrptw/algorithms/SolomonI1.hpp"
#include "vrptw/Neighborhoods.hpp"   // eval_insert
#include <limits>
#include <vector>

namespace vrptw {

Solution solomon_i1(const Instance& inst, const DistanceMatrix& dm, const I1Params& p) {
    const int n = static_cast<int>(inst.size());
    constexpr double kInf = std::numeric_limits<double>::max();

    Solution sol;
    std::vector<char> routed(static_cast<std::size_t>(n), 0);
    routed[0] = 1;
    int remaining = inst.num_customers();

    while (remaining > 0) {
        // seed the new route with the farthest unrouted customer from the depot
        int seed = -1;
        double best_seed = -1.0;
        for (int u = 1; u < n; ++u)
            if (!routed[u] && dm(0, u) > best_seed) { best_seed = dm(0, u); seed = u; }

        Route r;
        r.seq = {seed};
        r.recompute(inst, dm);
        routed[seed] = 1;
        --remaining;

        // greedily insert the best customer until none fits, then close route
        while (true) {
            int    best_u = -1, best_pos = -1;
            double best_c2 = -kInf;
            for (int u = 1; u < n; ++u) {
                if (routed[u]) continue;
                double best_c1 = kInf;
                int    pos_u = -1;
                for (int pos = 0; pos <= static_cast<int>(r.len()); ++pos) {
                    const InsertEval ie = eval_insert(inst, dm, r, pos, u);
                    if (!ie.feasible) continue;
                    const int pred = (pos == 0) ? 0 : r.seq[pos - 1];
                    const int succ = (pos == static_cast<int>(r.len())) ? 0 : r.seq[pos];
                    // ie.ddist = d(pred,u)+d(u,succ)-d(pred,succ); c11 adds the (1-mu) term
                    const double c11 = ie.ddist + (1.0 - p.mu) * dm(pred, succ);
                    const double c1  = p.alpha1 * c11;   // alpha2 == 0
                    if (c1 < best_c1) { best_c1 = c1; pos_u = pos; }
                }
                if (pos_u >= 0) {
                    const double c2 = p.lambda * dm(0, u) - best_c1;
                    if (c2 > best_c2) { best_c2 = c2; best_u = u; best_pos = pos_u; }
                }
            }
            if (best_u < 0) break;
            r.seq.insert(r.seq.begin() + best_pos, best_u);
            r.recompute(inst, dm);
            routed[best_u] = 1;
            --remaining;
        }

        sol.routes.push_back(std::move(r));
    }

    return sol;
}

} // namespace vrptw
