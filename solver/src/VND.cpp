#include "vrptw/algorithms/VND.hpp"
#include "vrptw/Evaluator.hpp"

namespace vrptw {

// Ordem por COMPLEXIDADE CRESCENTE, conforme Hansen & Mladenovic (2001) -- "the
// neighbourhoods should be ordered so that the simplest is explored first" -- e
// conforme o planejamento do projeto (docs/planejamento/neighborhood_selection_approach.md).
//
// A ordem abaixo vem do custo MEDIDO de uma varredura completa (teste
// neighborhood_scan_cost_ordering), nao da ordenacao teorica do planejamento:
// aquele documento ordena OITO operadores separados, enquanto esta implementacao
// FUNDE intra e inter em Relocate, Swap e Or-opt. A fusao muda o custo relativo
// -- o 2-opt intra varre R rotas, o Relocate varre R^2 pares -- e o 2-opt intra
// passa a ser o mais barato por duas ordens de grandeza.
//
//   2-opt intra   ~10 us     (intra: R * L^2)
//   Swap          ~170 us    (R^2/2 * L^2)
//   Relocate      ~320 us    (R^2 * L^2)
//   Or-opt        ~1000 us   (R^2 * L^2, cadeias de 2-3)
//   Cross-exch.   ~1700 us   (R^2 * L^2 * 9 combinacoes de segmento)
//
//   2-opt*        ~300 us    (R^2 * L^2, caudas de comprimento arbitrario)
//
// O 2-opt* e o oitavo movimento listado no relatorio parcial. A ablacao com
// Wilcoxon+Holm nas 28 instancias de treino mostrou que ele melhora em 8 e piora
// em NENHUMA (-1,291 pp em media), e por isso foi incorporado
// (docs/verificacao/03-vizinhancas.md).
std::vector<Neighborhood> default_vnd_order() {
    return all_neighborhoods();   // decisao 2.5: uma unica lista, lida tambem pela Tabu
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
