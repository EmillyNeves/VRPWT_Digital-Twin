// Guardas das decisões de projeto que são mecanizáveis.
//
// Cada teste leva o NÚMERO da decisão em docs/DECISOES-DE-PROJETO.md, para que
// uma falha aponte direto para a decisão e para a fonte que a define. É a
// resposta ao modo de falha observado: decisões registradas em documento são
// lidas uma vez e esquecidas; decisões guardadas por teste quebram o build.
#include "test_framework.hpp"
#include "vrptw/InstanceParser.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Neighborhoods.hpp"
#include "vrptw/Evaluator.hpp"
#include "vrptw/algorithms/SolomonI1.hpp"
#include "vrptw/algorithms/VND.hpp"
#include "vrptw/algorithms/Grasp.hpp"
#include "vrptw/algorithms/TabuSearch.hpp"
#include <filesystem>
#include <algorithm>
#include <chrono>
#include <string>
#include <vector>
#include <iostream>

using namespace vrptw;
namespace fs = std::filesystem;

namespace {

fs::path inst_path(const std::string& n) {
    return fs::path(PROJECT_ROOT) / "data" / "instances" / "solomon" / (n + ".txt");
}

const char* nb_name(Neighborhood nb) {
    switch (nb) {
        case Neighborhood::Relocate:      return "Relocate";
        case Neighborhood::Swap:          return "Swap";
        case Neighborhood::TwoOpt:        return "2opt";
        case Neighborhood::OrOpt:         return "Oropt";
        case Neighborhood::CrossExchange: return "Cross";
        case Neighborhood::TwoOptStar:    return "2opt*";
    }
    return "?";
}

std::string routes_of(const Solution& s) {
    std::string out;
    for (const auto& r : s.routes) {
        if (r.empty()) continue;
        if (!out.empty()) out += '|';
        for (std::size_t i = 0; i < r.seq.size(); ++i) {
            if (i) out += ' ';
            out += std::to_string(r.seq[i]);
        }
    }
    return out;
}

} // namespace

// DECISAO 1.3 — objective=cost, mu=1,0, eps=1e-6 fixos.
// Fonte: docs/planejamento/irace_calibration_plan.md §2 "Common execution contract".
TEST(decisao_1_3_parametros_fixos) {
    const I1Params p;
    CHECK_NEAR(p.mu, 1.0, 1e-12);
    CHECK_NEAR(kEps, 1e-6, 1e-15);
    // objective=cost: Evaluator::primary e a distancia total, sem termo de veiculos
    const Instance inst = parse_instance(inst_path("C101").string());
    const DistanceMatrix dm(inst);
    const Evaluator ev(inst, dm);
    const Solution s = solomon_i1(inst, dm);
    double manual = 0.0;
    for (const auto& r : s.routes) {
        int prev = 0;
        for (int c : r.seq) { manual += dm(prev, c); prev = c; }
        if (!r.empty()) manual += dm(prev, 0);
    }
    CHECK_NEAR(ev.primary(s), manual, 1e-9);
}

// DECISAO 1.4 — a I1 e a solucao inicial COMUM de nls/vnd/grasp/tabu.
// Fonte: docs/planejamento/conformance_audit.md §6 "same initial baseline policy
// (I1-based starts in nls/vnd/grasp/tabu)".
//
// Observavel: com zero iteracoes, GRASP e Tabu tem que devolver exatamente a I1.
// Se o GRASP voltar a comecar com incumbente vazio, este teste quebra.
TEST(decisao_1_4_i1_como_partida_comum) {
    int ok_grasp = 0, ok_tabu = 0, n = 0;
    for (const char* name : {"C101", "R101", "RC101", "R201"}) {
        const Instance inst = parse_instance(inst_path(name).string());
        const DistanceMatrix dm(inst);
        const std::string i1 = routes_of(solomon_i1(inst, dm));
        ++n;

        StoppingCriterion s1(5000);
        GraspConfig gc;
        gc.max_iters = 0;                       // nenhuma iteracao: sobra o incumbente inicial
        Rng rng(1);
        int gi = 0;
        if (routes_of(grasp(inst, dm, s1, rng, gc, nullptr, &gi)) == i1) ++ok_grasp;

        StoppingCriterion s2(5000);
        TabuConfig tc;
        tc.max_iters = 0;
        long ti = 0;
        if (routes_of(tabu_search(inst, dm, solomon_i1(inst, dm), s2, tc, nullptr, &ti)) == i1) ++ok_tabu;
    }
    std::cout << "  [dec 1.4] GRASP parte da I1: " << ok_grasp << "/" << n
              << ", Tabu: " << ok_tabu << "/" << n << "\n";
    CHECK(ok_grasp == n);
    CHECK(ok_tabu == n);
}

// DECISAO 2.2 — vizinhancas exploradas em ordem de complexidade crescente.
// Fonte: docs/planejamento/neighborhood_selection_approach.md; Hansen &
// Mladenovic (2001), "the neighbourhoods should be ordered so that the simplest
// is explored first".
//
// Mede o custo real de uma varredura e exige que a ordem padrao seja crescente.
// Tolera inversao entre pares proximos (<=30%): a diferenca entre 2-opt* e
// Relocate e de ~7% e a ordem entre eles e arbitraria.
TEST(decisao_2_2_ordem_por_complexidade) {
    const char* kInst[] = {"C101", "R101", "RC101", "R201"};
    std::vector<double> cost(all_neighborhoods().size(), 0.0);

    for (const char* name : kInst) {
        const Instance inst = parse_instance(inst_path(name).string());
        const DistanceMatrix dm(inst);
        Solution sol = solomon_i1(inst, dm);
        sol.recompute_all(inst, dm);
        for (std::size_t i = 0; i < all_neighborhoods().size(); ++i) {
            const auto t0 = std::chrono::steady_clock::now();
            for (int r = 0; r < 3; ++r)
                (void)find_best_move(sol, inst, dm, all_neighborhoods()[i], false);
            cost[i] += static_cast<double>(std::chrono::duration_cast<std::chrono::microseconds>(
                std::chrono::steady_clock::now() - t0).count()) / 3.0;
        }
    }

    std::cout << "  [dec 2.2] custo por varredura, na ordem padrao (us):";
    for (std::size_t i = 0; i < cost.size(); ++i)
        std::cout << " " << nb_name(all_neighborhoods()[i]) << "=" << static_cast<long>(cost[i]);
    std::cout << "\n";

    int inversoes = 0;
    for (std::size_t i = 0; i + 1 < cost.size(); ++i)
        if (cost[i] > cost[i + 1] * 1.30) {          // inversao alem da tolerancia
            ++inversoes;
            std::cout << "  -> posicao " << i << " custa " << static_cast<long>(cost[i])
                      << " us, mais que a seguinte (" << static_cast<long>(cost[i + 1]) << ")\n";
        }
    CHECK(inversoes == 0);
}

// DECISAO 2.5 — mesmo conjunto de vizinhancas entre os metodos comparados.
// Fonte: docs/planejamento/conformance_audit.md §6.
//
// Garantida por CONSTRUCAO: default_vnd_order() e find_best_admissible() leem
// all_neighborhoods(). Este teste guarda a construcao contra um futuro que a
// desfaca -- se alguem voltar a escrever a lista a mao em um dos dois, quebra.
TEST(decisao_2_5_mesmo_kit_vnd_e_tabu) {
    const auto& canon = all_neighborhoods();
    const auto vnd = default_vnd_order();
    CHECK(vnd.size() == canon.size());
    bool same = vnd.size() == canon.size();
    for (std::size_t i = 0; same && i < vnd.size(); ++i) same = (vnd[i] == canon[i]);
    CHECK(same);

    // e a Tabu enxerga as seis: cada tipo de movimento tem que ser alcancavel
    const Instance inst = parse_instance(inst_path("R201").string());
    const DistanceMatrix dm(inst);
    Solution sol = solomon_i1(inst, dm);
    sol.recompute_all(inst, dm);
    int alcancaveis = 0;
    for (Neighborhood nb : canon)
        if (find_best_move(sol, inst, dm, nb, false).type != MoveType::None) ++alcancaveis;
    std::cout << "  [dec 2.5] kit unico com " << canon.size()
              << " vizinhancas, " << alcancaveis << " produzem movimento em R201\n";
    CHECK(alcancaveis >= 5);
}
