#include "vrptw/algorithms/Grasp.hpp"
#include "vrptw/algorithms/SolomonI1.hpp"
#include "vrptw/Neighborhoods.hpp"   // eval_insert
#include "vrptw/Evaluator.hpp"
#include <limits>
#include <cmath>
#include <vector>

namespace vrptw {

namespace {
struct Cand { int u; int pos; double c2; };
}

Solution grasp_construct(const Instance& inst, const DistanceMatrix& dm, Rng& rng,
                         double alpha, const I1Params& p) {
    const int n = static_cast<int>(inst.size());
    constexpr double kInf = std::numeric_limits<double>::max();

    Solution sol;
    std::vector<char> routed(static_cast<std::size_t>(n), 0);
    routed[0] = 1;
    int remaining = inst.num_customers();

    while (remaining > 0) {
        const int seed = i1_select_seed(inst, dm, routed, p.seed);
        if (seed < 0) break;

        Route r;
        r.seq = {seed};
        r.recompute(inst, dm);
        routed[static_cast<std::size_t>(seed)] = 1;
        --remaining;

        while (true) {
            // best feasible insertion (c1) and selection value (c2) per unrouted
            // customer -- the SAME Solomon criterion the deterministic I1 uses
            std::vector<Cand> cands;
            I1Candidate ic;
            for (int u = 1; u < n; ++u) {
                if (routed[static_cast<std::size_t>(u)]) continue;
                if (i1_best_insertion(inst, dm, r, u, p, ic))
                    cands.push_back({ic.u, ic.pos, ic.c2});
            }
            if (cands.empty()) break;

            // value-based RCL on c2 (higher is better): c2 >= cmax - alpha*(cmax-cmin)
            double cmax = -kInf, cmin = kInf;
            for (const auto& c : cands) { cmax = std::max(cmax, c.c2); cmin = std::min(cmin, c.c2); }
            const double thr = cmax - alpha * (cmax - cmin);
            std::vector<const Cand*> rcl;
            for (const auto& c : cands) if (c.c2 >= thr - 1e-12) rcl.push_back(&c);

            const Cand* chosen = rcl[static_cast<std::size_t>(rng.uniform_int(0, static_cast<int>(rcl.size()) - 1))];
            r.seq.insert(r.seq.begin() + chosen->pos, chosen->u);
            r.recompute(inst, dm);
            routed[chosen->u] = 1;
            --remaining;
        }
        sol.routes.push_back(std::move(r));
    }
    return sol;
}

namespace {
int sample_index(const std::vector<double>& p, Rng& rng) {
    const double rsel = rng.uniform_real(0.0, 1.0);
    double acc = 0.0;
    for (std::size_t i = 0; i < p.size(); ++i) { acc += p[i]; if (rsel <= acc) return static_cast<int>(i); }
    return static_cast<int>(p.size()) - 1;
}
}

Solution grasp(const Instance& inst, const DistanceMatrix& dm, StoppingCriterion& stop,
               Rng& rng, const GraspConfig& cfg, Logger* log, int* out_iters) {
    const Evaluator ev(inst, dm);

    std::vector<double> A = cfg.alpha_set;
    if (cfg.reactive && A.empty())
        A = {0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50};
    std::vector<double> prob(A.size(), A.empty() ? 0.0 : 1.0 / A.size());
    std::vector<double> sum_cost(A.size(), 0.0);
    std::vector<int>    count(A.size(), 0);

    // A I1 pura entra como INCUMBENTE INICIAL, de modo que o GRASP herda a mesma
    // solucao de partida que o VND e a Busca Tabu recebem. E a politica declarada
    // em docs/planejamento/conformance_audit.md -- "same initial baseline policy:
    // I1-based starts in nls/vnd/grasp/tabu" -- e o que a versao anterior do
    // projeto fazia. Sem isto, o GRASP so conhece construcoes randomizadas e a
    // relacao GRASP <= I1 fica sendo uma observacao empirica em vez de uma
    // garantia. Nao vale semear com I1+VND: isso tornaria GRASP <= VND um
    // teorema e esvaziaria justamente a comparacao que se quer medir.
    Solution best = solomon_i1(inst, dm, cfg.i1);
    best.recompute_all(inst, dm);
    double best_cost = ev.primary(best);
    bool   have = true;
    int    snap_idx = 0;
    int    iter = 0;
    int    no_improve = 0;   // consecutive iterations without improving the incumbent

    if (log) log->on_improve(0, best_cost, 0);   // curva anytime comeca na I1, em t=0

    while (!stop.should_stop()) {                       // time budget acts only as a safety cap
        if (cfg.max_iters >= 0 && iter >= cfg.max_iters) break;

        double alpha = cfg.alpha;
        int ai = -1;
        if (cfg.reactive) {
            ai = (iter < static_cast<int>(A.size())) ? iter        // try each alpha once first
                                                     : sample_index(prob, rng);
            alpha = A[static_cast<std::size_t>(ai)];
        }

        Solution s = grasp_construct(inst, dm, rng, alpha, cfg.i1);
        s = vnd_local_search(inst, dm, std::move(s), cfg.vnd, nullptr, &stop, nullptr);
        const double c = ev.primary(s);

        if (cfg.reactive && ai >= 0) { sum_cost[static_cast<std::size_t>(ai)] += c; ++count[static_cast<std::size_t>(ai)]; }

        if (!have || c < best_cost - 1e-9) {
            best_cost = c;
            best = s;
            have = true;
            no_improve = 0;                                                   // incumbent improved: reset
            if (log) {
                const long ms = stop.elapsed_ms();
                log->on_improve(ms, c, iter);
                log->on_move(++snap_idx, ms, c, best, "incumbent");
            }
            if (cfg.target >= 0.0 && best_cost <= cfg.target + 1e-6) break;   // target reached (TTT)
        } else {
            ++no_improve;
        }
        ++iter;

        // PRIMARY stopping criterion: K iterations without improvement.
        if (cfg.max_no_improve >= 0 && no_improve >= cfg.max_no_improve) break;

        if (cfg.reactive && (iter % cfg.block) == 0) {
            // Prais & Ribeiro: q_i = (best/avg_i)^delta, p_i = q_i / sum q
            std::vector<double> q(A.size(), 0.0);
            double sumq = 0.0;
            for (std::size_t i = 0; i < A.size(); ++i) {
                const double avg = count[i] > 0 ? sum_cost[i] / count[i] : best_cost * 2.0;
                q[i] = std::pow(best_cost / avg, cfg.delta);
                sumq += q[i];
            }
            for (std::size_t i = 0; i < A.size(); ++i) prob[i] = q[i] / sumq;
        }
    }
    if (out_iters) *out_iters = iter;
    best.recompute_all(inst, dm);
    return best;
}

} // namespace vrptw
