#include "vrptw/Neighborhoods.hpp"
#include "vrptw/Route.hpp"   // kEps
#include <algorithm>
#include <limits>

// Internal note: every operator reports candidate moves to a Best tracker. With
// a MoveFilter (Tabu), non-improving moves are allowed and tabu moves are
// rejected unless they aspirate; without one, only improving moves count.

namespace vrptw {

namespace {
constexpr double kImprove = 1e-7;   // a move must reduce distance by at least this

// new sequence = s with `len` elements removed starting at i
std::vector<int> with_removed(const std::vector<int>& s, int i, int len) {
    std::vector<int> r;
    r.reserve(s.size());
    for (int k = 0; k < static_cast<int>(s.size()); ++k)
        if (k < i || k >= i + len) r.push_back(s[k]);
    return r;
}

// insert chain[0..len) into s at pos, reversed if rev
void insert_chain(std::vector<int>& s, int pos, const int* chain, int len, bool rev) {
    if (!rev) s.insert(s.begin() + pos, chain, chain + len);
    else for (int k = 0; k < len; ++k) s.insert(s.begin() + pos, chain[k]);
}

struct Best {
    Move              move;
    double            best_delta;
    bool              first;
    bool              done = false;
    const MoveFilter* filt;

    Best(const MoveFilter* f, bool first_improvement)
        : best_delta((f && f->allow_nonimproving) ? std::numeric_limits<double>::max() : -kImprove),
          first(first_improvement), filt(f) {}

    void consider(Move m) {
        if (!m.feasible) return;
        if (filt && filt->is_tabu && filt->is_tabu(m)) {
            // tabu unless aspiration (resulting cost beats the global best)
            if (!(filt->cur_cost + m.delta < filt->best_cost - 1e-7)) return;
        }
        if (m.delta < best_delta) {
            best_delta = m.delta;
            m.feasible = true;
            move = m;
            if (first) done = true;
        }
    }
};
} // namespace

SeqEval evaluate_seq(const Instance& inst, const DistanceMatrix& dm, const std::vector<int>& seq) {
    SeqEval e;
    if (seq.empty()) return e;
    double t = inst.depot().ready;
    int prev = 0;
    for (int c : seq) {
        e.distance += dm(prev, c);          // cost
        t += dm.time(prev, c);              // schedule (== distance by default)
        const Customer& cust = inst.node(c);
        if (t < cust.ready) t = cust.ready;
        if (t > cust.due + kEps) e.feasible = false;
        t += cust.service;
        e.load += cust.demand;
        prev = c;
    }
    e.distance += dm(prev, 0);
    t += dm.time(prev, 0);
    if (t > inst.depot().due + kEps) e.feasible = false;
    if (e.load > inst.capacity + kEps) e.feasible = false;
    return e;
}

InsertEval eval_insert(const Instance& inst, const DistanceMatrix& dm,
                       const Route& r, int pos, int u) {
    InsertEval ie;
    const int m = static_cast<int>(r.seq.size());
    const int pred = (pos == 0) ? 0 : r.seq[pos - 1];
    const int succ = (pos == m) ? 0 : r.seq[pos];
    ie.ddist = dm(pred, u) + dm(u, succ) - dm(pred, succ);

    const Customer& cu = inst.node(u);
    if (r.load + cu.demand > inst.capacity + kEps) return ie;   // capacity

    const double dep_pred = (pos == 0) ? inst.depot().ready : r.departure[pos - 1];
    const double arr_u    = dep_pred + dm.time(pred, u);        // schedule uses the time matrix
    const double start_u  = std::max(arr_u, cu.ready);
    if (start_u > cu.due + kEps) return ie;                     // u's own window

    const double dep_u    = start_u + cu.service;
    const double arr_succ = dep_u + dm.time(u, succ);
    if (pos == m) {
        if (arr_succ > inst.depot().due + kEps) return ie;      // return to depot
    } else {
        const Customer& cs = inst.node(succ);
        const double new_start_succ = std::max(arr_succ, cs.ready);
        const double shift = new_start_succ - r.start[pos];     // push-forward at succ
        if (shift > r.tw_slack[pos] + kEps) return ie;
    }
    ie.feasible = true;
    return ie;
}

// ---------------------------------------------------------------- Relocate
static Move find_relocate(const Solution& sol, const Instance& inst,
                          const DistanceMatrix& dm, bool first, const MoveFilter* filt) {
    Best B(filt, first);
    const int R = static_cast<int>(sol.routes.size());
    for (int r1 = 0; r1 < R && !B.done; ++r1) {
        const auto& s1 = sol.routes[r1].seq;
        if (s1.empty()) continue;
        const double old1 = sol.routes[r1].distance;
        for (int i1 = 0; i1 < static_cast<int>(s1.size()) && !B.done; ++i1) {
            const int c = s1[i1];
            const std::vector<int> src = with_removed(s1, i1, 1);
            const SeqEval eSrc = evaluate_seq(inst, dm, src);   // for inter case
            for (int r2 = 0; r2 < R && !B.done; ++r2) {
                if (r2 == r1) {
                    for (int adj = 0; adj <= static_cast<int>(src.size()); ++adj) {
                        if (adj == i1) continue;               // identity
                        std::vector<int> cand = src;
                        cand.insert(cand.begin() + adj, c);
                        const SeqEval e = evaluate_seq(inst, dm, cand);
                        B.consider(Move{MoveType::Relocate, r1, i1, r2, adj, 1, 1, false,
                                        e.feasible, e.distance - old1});
                        if (B.done) break;
                    }
                } else {
                    if (!eSrc.feasible) continue;              // source must stay feasible
                    const auto& s2 = sol.routes[r2].seq;
                    const double old2 = sol.routes[r2].distance;
                    for (int i2 = 0; i2 <= static_cast<int>(s2.size()); ++i2) {
                        std::vector<int> cand = s2;
                        cand.insert(cand.begin() + i2, c);
                        const SeqEval e = evaluate_seq(inst, dm, cand);
                        B.consider(Move{MoveType::Relocate, r1, i1, r2, i2, 1, 1, false,
                                        e.feasible, (eSrc.distance + e.distance) - (old1 + old2)});
                        if (B.done) break;
                    }
                }
            }
        }
    }
    return B.move;
}

// -------------------------------------------------------------------- Swap
static Move find_swap(const Solution& sol, const Instance& inst,
                      const DistanceMatrix& dm, bool first, const MoveFilter* filt) {
    Best B(filt, first);
    const int R = static_cast<int>(sol.routes.size());
    for (int r1 = 0; r1 < R && !B.done; ++r1) {
        const auto& s1 = sol.routes[r1].seq;
        if (s1.empty()) continue;
        const double old1 = sol.routes[r1].distance;
        for (int i1 = 0; i1 < static_cast<int>(s1.size()) && !B.done; ++i1) {
            for (int r2 = r1; r2 < R && !B.done; ++r2) {
                const auto& s2 = sol.routes[r2].seq;
                if (s2.empty()) continue;
                const int i2start = (r2 == r1) ? i1 + 1 : 0;
                const double old2 = sol.routes[r2].distance;
                for (int i2 = i2start; i2 < static_cast<int>(s2.size()) && !B.done; ++i2) {
                    if (r2 == r1) {
                        std::vector<int> cand = s1;
                        std::swap(cand[i1], cand[i2]);
                        const SeqEval e = evaluate_seq(inst, dm, cand);
                        B.consider(Move{MoveType::Swap, r1, i1, r2, i2, 1, 1, false,
                                        e.feasible, e.distance - old1});
                    } else {
                        std::vector<int> c1 = s1, c2 = s2;
                        std::swap(c1[i1], c2[i2]);
                        const SeqEval e1 = evaluate_seq(inst, dm, c1);
                        const SeqEval e2 = evaluate_seq(inst, dm, c2);
                        B.consider(Move{MoveType::Swap, r1, i1, r2, i2, 1, 1, false,
                                        e1.feasible && e2.feasible,
                                        (e1.distance + e2.distance) - (old1 + old2)});
                    }
                }
            }
        }
    }
    return B.move;
}

// --------------------------------------------------------------- 2-opt intra
static Move find_twoopt(const Solution& sol, const Instance& inst,
                        const DistanceMatrix& dm, bool first, const MoveFilter* filt) {
    Best B(filt, first);
    const int R = static_cast<int>(sol.routes.size());
    for (int r = 0; r < R && !B.done; ++r) {
        const auto& s = sol.routes[r].seq;
        const int m = static_cast<int>(s.size());
        if (m < 2) continue;
        const double old = sol.routes[r].distance;
        for (int i = 0; i < m - 1 && !B.done; ++i) {
            for (int j = i + 1; j < m && !B.done; ++j) {
                std::vector<int> cand = s;
                std::reverse(cand.begin() + i, cand.begin() + j + 1);
                const SeqEval e = evaluate_seq(inst, dm, cand);
                B.consider(Move{MoveType::TwoOpt, r, i, r, j, 1, 1, false,
                                e.feasible, e.distance - old});
            }
        }
    }
    return B.move;
}

// ------------------------------------------------------------------- Or-opt
static Move find_oropt(const Solution& sol, const Instance& inst,
                       const DistanceMatrix& dm, bool first, const MoveFilter* filt) {
    Best B(filt, first);
    const int R = static_cast<int>(sol.routes.size());
    for (int L = 2; L <= 3 && !B.done; ++L) {
        for (int r1 = 0; r1 < R && !B.done; ++r1) {
            const auto& s1 = sol.routes[r1].seq;
            if (static_cast<int>(s1.size()) < L) continue;
            const double old1 = sol.routes[r1].distance;
            for (int i1 = 0; i1 + L <= static_cast<int>(s1.size()) && !B.done; ++i1) {
                int chain[3] = {s1[i1], (L > 1 ? s1[i1 + 1] : 0), (L > 2 ? s1[i1 + 2] : 0)};
                const std::vector<int> src = with_removed(s1, i1, L);
                const SeqEval eSrc = evaluate_seq(inst, dm, src);
                for (int r2 = 0; r2 < R && !B.done; ++r2) {
                    for (int rev = 0; rev < 2 && !B.done; ++rev) {
                        if (r2 == r1) {
                            for (int adj = 0; adj <= static_cast<int>(src.size()) && !B.done; ++adj) {
                                if (adj == i1 && rev == 0) continue;   // identity
                                std::vector<int> cand = src;
                                insert_chain(cand, adj, chain, L, rev != 0);
                                const SeqEval e = evaluate_seq(inst, dm, cand);
                                B.consider(Move{MoveType::OrOpt, r1, i1, r2, adj, L, 1,
                                                rev != 0, e.feasible, e.distance - old1});
                            }
                        } else {
                            if (!eSrc.feasible) continue;
                            const auto& s2 = sol.routes[r2].seq;
                            const double old2 = sol.routes[r2].distance;
                            for (int i2 = 0; i2 <= static_cast<int>(s2.size()) && !B.done; ++i2) {
                                std::vector<int> cand = s2;
                                insert_chain(cand, i2, chain, L, rev != 0);
                                const SeqEval e = evaluate_seq(inst, dm, cand);
                                B.consider(Move{MoveType::OrOpt, r1, i1, r2, i2, L, 1,
                                                rev != 0, eSrc.feasible && e.feasible,
                                                (eSrc.distance + e.distance) - (old1 + old2)});
                            }
                        }
                    }
                }
            }
        }
    }
    return B.move;
}

// ------------------------------------------------------------- Cross-exchange
static Move find_cross(const Solution& sol, const Instance& inst,
                       const DistanceMatrix& dm, bool first, const MoveFilter* filt) {
    Best B(filt, first);
    const int R = static_cast<int>(sol.routes.size());
    for (int r1 = 0; r1 < R && !B.done; ++r1) {
        const auto& s1 = sol.routes[r1].seq;
        if (s1.empty()) continue;
        const double old1 = sol.routes[r1].distance;
        for (int r2 = r1 + 1; r2 < R && !B.done; ++r2) {
            const auto& s2 = sol.routes[r2].seq;
            if (s2.empty()) continue;
            const double old2 = sol.routes[r2].distance;
            const int n1 = static_cast<int>(s1.size()), n2 = static_cast<int>(s2.size());
            for (int L1 = 1; L1 <= 3 && L1 <= n1 && !B.done; ++L1) {
                for (int i1 = 0; i1 + L1 <= n1 && !B.done; ++i1) {
                    for (int L2 = 1; L2 <= 3 && L2 <= n2 && !B.done; ++L2) {
                        for (int i2 = 0; i2 + L2 <= n2 && !B.done; ++i2) {
                            std::vector<int> c1, c2;
                            c1.reserve(n1 - L1 + L2);
                            c2.reserve(n2 - L2 + L1);
                            c1.insert(c1.end(), s1.begin(), s1.begin() + i1);
                            c1.insert(c1.end(), s2.begin() + i2, s2.begin() + i2 + L2);
                            c1.insert(c1.end(), s1.begin() + i1 + L1, s1.end());
                            c2.insert(c2.end(), s2.begin(), s2.begin() + i2);
                            c2.insert(c2.end(), s1.begin() + i1, s1.begin() + i1 + L1);
                            c2.insert(c2.end(), s2.begin() + i2 + L2, s2.end());
                            const SeqEval e1 = evaluate_seq(inst, dm, c1);
                            const SeqEval e2 = evaluate_seq(inst, dm, c2);
                            B.consider(Move{MoveType::CrossExchange, r1, i1, r2, i2, L1, L2,
                                            false, e1.feasible && e2.feasible,
                                            (e1.distance + e2.distance) - (old1 + old2)});
                        }
                    }
                }
            }
        }
    }
    return B.move;
}

Move find_best_move(const Solution& sol, const Instance& inst, const DistanceMatrix& dm,
                    Neighborhood nb, bool first_improvement) {
    switch (nb) {
        case Neighborhood::Relocate:      return find_relocate(sol, inst, dm, first_improvement, nullptr);
        case Neighborhood::Swap:          return find_swap(sol, inst, dm, first_improvement, nullptr);
        case Neighborhood::TwoOpt:        return find_twoopt(sol, inst, dm, first_improvement, nullptr);
        case Neighborhood::OrOpt:         return find_oropt(sol, inst, dm, first_improvement, nullptr);
        case Neighborhood::CrossExchange: return find_cross(sol, inst, dm, first_improvement, nullptr);
    }
    return Move{};
}

Move find_best_admissible(const Solution& sol, const Instance& inst,
                          const DistanceMatrix& dm, const MoveFilter& filter) {
    const Move cands[] = {
        find_relocate(sol, inst, dm, false, &filter),
        find_swap(sol, inst, dm, false, &filter),
        find_twoopt(sol, inst, dm, false, &filter),
        find_oropt(sol, inst, dm, false, &filter),
        find_cross(sol, inst, dm, false, &filter),
    };
    Move best;
    double bd = filter.allow_nonimproving ? std::numeric_limits<double>::max() : -kImprove;
    for (const Move& m : cands)
        if (m.type != MoveType::None && m.delta < bd) { bd = m.delta; best = m; }
    return best;
}

// ------------------------------------------------------------------- apply
void apply_move(Solution& sol, const Move& mv, const Instance& inst, const DistanceMatrix& dm) {
    switch (mv.type) {
        case MoveType::Relocate: {
            const int c = sol.routes[mv.r1].seq[mv.i1];
            if (mv.r1 == mv.r2) {
                std::vector<int> s = with_removed(sol.routes[mv.r1].seq, mv.i1, 1);
                s.insert(s.begin() + mv.i2, c);
                sol.routes[mv.r1].seq = std::move(s);
                sol.routes[mv.r1].recompute(inst, dm);
            } else {
                sol.routes[mv.r1].seq = with_removed(sol.routes[mv.r1].seq, mv.i1, 1);
                sol.routes[mv.r2].seq.insert(sol.routes[mv.r2].seq.begin() + mv.i2, c);
                sol.routes[mv.r1].recompute(inst, dm);
                sol.routes[mv.r2].recompute(inst, dm);
            }
            break;
        }
        case MoveType::Swap: {
            if (mv.r1 == mv.r2) {
                std::swap(sol.routes[mv.r1].seq[mv.i1], sol.routes[mv.r1].seq[mv.i2]);
                sol.routes[mv.r1].recompute(inst, dm);
            } else {
                std::swap(sol.routes[mv.r1].seq[mv.i1], sol.routes[mv.r2].seq[mv.i2]);
                sol.routes[mv.r1].recompute(inst, dm);
                sol.routes[mv.r2].recompute(inst, dm);
            }
            break;
        }
        case MoveType::TwoOpt: {
            auto& s = sol.routes[mv.r1].seq;
            std::reverse(s.begin() + mv.i1, s.begin() + mv.i2 + 1);
            sol.routes[mv.r1].recompute(inst, dm);
            break;
        }
        case MoveType::OrOpt: {
            const auto& s1 = sol.routes[mv.r1].seq;
            int chain[3] = {s1[mv.i1], (mv.seg > 1 ? s1[mv.i1 + 1] : 0),
                            (mv.seg > 2 ? s1[mv.i1 + 2] : 0)};
            if (mv.r1 == mv.r2) {
                std::vector<int> s = with_removed(s1, mv.i1, mv.seg);
                insert_chain(s, mv.i2, chain, mv.seg, mv.rev);
                sol.routes[mv.r1].seq = std::move(s);
                sol.routes[mv.r1].recompute(inst, dm);
            } else {
                sol.routes[mv.r1].seq = with_removed(s1, mv.i1, mv.seg);
                insert_chain(sol.routes[mv.r2].seq, mv.i2, chain, mv.seg, mv.rev);
                sol.routes[mv.r1].recompute(inst, dm);
                sol.routes[mv.r2].recompute(inst, dm);
            }
            break;
        }
        case MoveType::CrossExchange: {
            const auto s1 = sol.routes[mv.r1].seq;   // copies
            const auto s2 = sol.routes[mv.r2].seq;
            std::vector<int> c1, c2;
            c1.insert(c1.end(), s1.begin(), s1.begin() + mv.i1);
            c1.insert(c1.end(), s2.begin() + mv.i2, s2.begin() + mv.i2 + mv.seg2);
            c1.insert(c1.end(), s1.begin() + mv.i1 + mv.seg, s1.end());
            c2.insert(c2.end(), s2.begin(), s2.begin() + mv.i2);
            c2.insert(c2.end(), s1.begin() + mv.i1, s1.begin() + mv.i1 + mv.seg);
            c2.insert(c2.end(), s2.begin() + mv.i2 + mv.seg2, s2.end());
            sol.routes[mv.r1].seq = std::move(c1);
            sol.routes[mv.r2].seq = std::move(c2);
            sol.routes[mv.r1].recompute(inst, dm);
            sol.routes[mv.r2].recompute(inst, dm);
            break;
        }
        case MoveType::None: break;
    }
}

} // namespace vrptw
