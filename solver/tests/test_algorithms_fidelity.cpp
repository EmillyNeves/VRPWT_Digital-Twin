// Verificação de fidelidade dos algoritmos de melhoria (Etapa 2).
//
// Um teste por algoritmo, cobrindo a propriedade ESTRUTURAL que a fonte canônica
// garante e que não depende da qualidade da solução. Ver docs/verificacao/.
#include "test_framework.hpp"
#include "vrptw/InstanceParser.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Evaluator.hpp"
#include "vrptw/Validator.hpp"
#include "vrptw/Neighborhoods.hpp"
#include "vrptw/algorithms/SolomonI1.hpp"
#include "vrptw/algorithms/VND.hpp"
#include "vrptw/algorithms/Grasp.hpp"
#include "vrptw/algorithms/TabuSearch.hpp"
#include <filesystem>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <string>
#include <vector>
#include <iostream>
#include <chrono>

using namespace vrptw;
namespace fs = std::filesystem;

namespace {

std::vector<fs::path> all_instances() {
    std::vector<fs::path> v;
    const fs::path dir = fs::path(PROJECT_ROOT) / "data" / "instances" / "solomon";
    for (const auto& e : fs::directory_iterator(dir))
        if (e.path().extension() == ".txt") v.push_back(e.path());
    std::sort(v.begin(), v.end());
    return v;
}

fs::path instance_of(const std::string& name) {
    return fs::path(PROJECT_ROOT) / "data" / "instances" / "solomon" / (name + ".txt");
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

// ---------------------------------------------------------------------- VND
// Hansen & Mladenovic (2001): o VND termina em um otimo local com relacao a
// TODAS as vizinhancas, nao apenas a ultima. E a definicao do metodo, e ate
// agora nenhum teste a verificava (test_vnd.cpp so checa monotonicidade).
TEST(vnd_is_local_optimum_in_all_neighborhoods) {
    const Neighborhood kAll[] = {Neighborhood::Relocate, Neighborhood::Swap,
                                 Neighborhood::TwoOpt, Neighborhood::OrOpt,
                                 Neighborhood::CrossExchange, Neighborhood::TwoOptStar};
    int tested = 0, clean = 0;
    for (const auto& ip : all_instances()) {
        const Instance inst = parse_instance(ip.string());
        const DistanceMatrix dm(inst);
        Solution sol = vnd_local_search(inst, dm, solomon_i1(inst, dm), VndConfig{});
        sol.recompute_all(inst, dm);
        ++tested;

        bool ok = true;
        for (Neighborhood nb : kAll) {
            const Move m = find_best_move(sol, inst, dm, nb, false);
            if (m.type != MoveType::None && m.delta < -1e-7) {
                ok = false;
                std::cout << "  -> " << ip.stem().string() << ": movimento melhorante restante em "
                          << move_name(m.type) << " (delta=" << m.delta << ")\n";
                break;
            }
        }
        CHECK(ok);
        if (ok) ++clean;
    }
    std::cout << "  [VND] otimo local em TODAS as 6 vizinhancas: " << clean << "/" << tested << "\n";
    CHECK(tested == 56);
    CHECK(clean == 56);
}

// -------------------------------------------------------------------- GRASP
// Feo & Resende (1995): com alpha = 0 a RCL colapsa no argmax de c2, e a
// construcao gulosa-aleatorizada degenera na construcao gulosa pura -- que aqui
// e exatamente a I1. E a checagem natural de que os dois compartilham o criterio.
// Ressalva: havendo empate no argmax, a RCL tem mais de um elemento e o RNG
// escolhe, enquanto a I1 fica com o primeiro; por isso contamos em vez de exigir
// igualdade cega.
TEST(grasp_alpha0_degenerates_to_i1) {
    int tested = 0, identical = 0, seed_dependent = 0, unexplained = 0;
    for (const auto& ip : all_instances()) {
        const Instance inst = parse_instance(ip.string());
        const DistanceMatrix dm(inst);
        ++tested;

        Rng r1(12345);
        const std::string g1 = routes_of(grasp_construct(inst, dm, r1, 0.0));
        const std::string i1 = routes_of(solomon_i1(inst, dm));

        Rng probe(12345);
        CHECK(validate(inst, dm, grasp_construct(inst, dm, probe, 0.0)).feasible);

        if (g1 == i1) { ++identical; continue; }

        // Divergiu. A UNICA fonte legitima de divergencia com alpha=0 e o RNG
        // escolhendo entre candidatos empatados no argmax de c2. Se trocar a
        // semente muda o resultado, o empate esta confirmado; se nao muda, ha
        // uma diferenca real entre a construcao do GRASP e a I1.
        bool varies = false;
        for (std::uint64_t s : {2ULL, 7ULL, 99ULL, 4242ULL}) {
            Rng r(s);
            if (routes_of(grasp_construct(inst, dm, r, 0.0)) != g1) { varies = true; break; }
        }
        if (varies) ++seed_dependent;
        else {
            ++unexplained;
            std::cout << "  -> " << ip.stem().string()
                      << ": difere da I1 e NAO depende da semente\n";
        }
    }
    std::cout << "  [GRASP a=0] identicas a I1: " << identical << "/" << tested
              << ", divergentes por empate no argmax: " << seed_dependent
              << ", inexplicadas: " << unexplained << "\n";
    CHECK(tested == 56);
    CHECK(unexplained == 0);                       // toda divergencia tem que ser empate
    CHECK(identical + seed_dependent == tested);
}

// --------------------------------------------------------------- Busca Tabu
// Glover (1989/1990): o tenure t proibe o atributo por EXATAMENTE t iteracoes.
// A implementacao original gravava tabu_until = iter + tenure e testava
// tabu_until > iter', o que proibia por t-1 -- com t=1 nao proibia nada, ficando
// identico a t=0. Corrigido com o +1. Este teste guarda a convencao: t=0 nao
// proibe nada, t=1 ja proibe, e os dois TEM que diferir.
// A convencao NAO e observavel comparando t=0 com t=1: bloquear UM cliente por
// UMA iteracao praticamente nunca muda o argmin entre ~10^4 movimentos
// candidatos (medido: t=0,1,2 dao resultado identico em C101/R101/RC101/R201).
// O que se verifica e que a memoria de recencia tem efeito detectavel em valores
// realistas de tenure -- se nao tivesse, a lista tabu seria decorativa.
TEST(tabu_tenure_has_detectable_effect) {
    int differ = 0, tested = 0;
    for (const char* name : {"R201", "RC101"}) {
        const Instance inst = parse_instance(instance_of(name).string());
        const DistanceMatrix dm(inst);
        const Solution start = solomon_i1(inst, dm);
        const Evaluator ev(inst, dm);

        auto run = [&](int tenure) {
            StoppingCriterion stop(30000);
            TabuConfig cfg;
            cfg.tenure = tenure;
            cfg.max_iters = 200;
            long it = 0;
            return ev.primary(tabu_search(inst, dm, start, stop, cfg, nullptr, &it));
        };
        const double t0 = run(0), t39 = run(39);
        ++tested;
        if (std::fabs(t0 - t39) > 1e-6) ++differ;
        std::cout << "  [Tabu] " << name << ": tenure=0 -> " << t0
                  << ", tenure=39 -> " << t39 << "\n";
    }
    CHECK(tested == 2);
    CHECK(differ == 2);
}

// ASPIRACAO POR OMISSAO (Glover, Tabela 2.8). Com tenure alto TODOS os
// movimentos podem ficar tabu. Sem a aspiracao por omissao a busca encerra ali:
// medido com o tenure calibrado (39), C101 parava na iteracao 17 e C201 na 26,
// de ~1400 -- uma truncagem de 50 a 80x que o irace calibraria como se fosse
// comportamento normal. Este teste impede a reincidencia.
TEST(tabu_aspiration_by_default_prevents_truncation) {
    constexpr long kIters = 400;
    int ok = 0, tested = 0;
    for (const char* name : {"C101", "C201"}) {
        const Instance inst = parse_instance(instance_of(name).string());
        const DistanceMatrix dm(inst);

        StoppingCriterion stop(120000);
        TabuConfig cfg;
        cfg.tenure = 39;
        cfg.max_iters = static_cast<int>(kIters);
        long it = 0;
        const Solution out = tabu_search(inst, dm, solomon_i1(inst, dm), stop, cfg, nullptr, &it);
        ++tested;
        CHECK(validate(inst, dm, out).feasible);
        CHECK(it >= kIters - 5);            // nao pode encerrar por lista tabu cheia
        if (it >= kIters - 5) ++ok;
        std::cout << "  [Tabu] " << name << ": " << it << "/" << kIters << " iteracoes\n";
    }
    CHECK(ok == tested);
}

// A Tabu devolve o MELHOR incumbente encontrado, nunca o ultimo visitado -- e o
// que justifica aceitar movimentos de piora. Verificamos que o resultado nunca e
// pior que o ponto de partida, mesmo com tenure alto e muitas iteracoes.
TEST(tabu_returns_best_incumbent) {
    const Evaluator* dummy = nullptr; (void)dummy;
    int ok = 0, tested = 0;
    for (const char* name : {"C101", "R101", "RC101", "C201", "R201"}) {
        const Instance inst = parse_instance(instance_of(name).string());
        const DistanceMatrix dm(inst);
        const Evaluator ev(inst, dm);
        const Solution start = solomon_i1(inst, dm);

        StoppingCriterion stop(10000);
        TabuConfig cfg;
        cfg.tenure = 39;              // o valor calibrado
        cfg.max_iters = 500;
        long it = 0;
        const Solution out = tabu_search(inst, dm, start, stop, cfg, nullptr, &it);
        ++tested;
        CHECK(validate(inst, dm, out).feasible);
        CHECK(ev.primary(out) <= ev.primary(start) + 1e-6);
        if (ev.primary(out) <= ev.primary(start) + 1e-6) ++ok;
    }
    std::cout << "  [Tabu] nunca pior que a partida: " << ok << "/" << tested << "\n";
    CHECK(ok == tested);
}

// ------------------------------------------------------- GRASP reativo
// Prais & Ribeiro (2000): as probabilidades dos alpha sao reponderadas a cada
// `block` iteracoes. Para o mecanismo REAGIR, uma execucao precisa conter varias
// reponderacoes -- do contrario o metodo e apenas um GRASP com alpha sorteado.
//
// Com `block` em iteracoes ABSOLUTAS isso depende da escala do criterio de
// parada, e foi violado na configuracao calibrada: block=199 com K=250 produz
// UMA reponderacao por execucao. A parametrizacao correta e block = frac * K,
// que fixa o NUMERO de reponderacoes. Este teste impede a reincidencia.
TEST(reactive_grasp_actually_reacts) {
    constexpr double kFrac = 0.1;    // 10% de K  ->  ~10 reponderacoes
    constexpr int    kK    = 60;     // K pequeno para o teste ser barato
    int tested = 0, ok = 0;

    for (const char* name : {"C101", "R101"}) {
        const Instance inst = parse_instance(instance_of(name).string());
        const DistanceMatrix dm(inst);

        GraspConfig cfg;
        cfg.reactive       = true;
        cfg.max_no_improve = kK;
        cfg.block          = std::max(1, static_cast<int>(std::lround(kFrac * kK)));

        StoppingCriterion stop(120000);
        Rng rng(1);
        int iters = 0;
        const Solution s = grasp(inst, dm, stop, rng, cfg, nullptr, &iters);
        const int updates = iters / cfg.block;
        ++tested;

        CHECK(validate(inst, dm, s).feasible);
        CHECK(updates >= 5);
        if (updates >= 5) ++ok;
        std::cout << "  [rGRASP] " << name << ": iters=" << iters
                  << " block=" << cfg.block << " reponderacoes=" << updates << "\n";
    }
    CHECK(tested == 2);
    CHECK(ok == tested);
}

// ------------------------------------------------- ordem das vizinhancas
// Hansen & Mladenovic (2001): "the neighbourhoods should be ordered so that the
// simplest is explored first". O planejamento do projeto
// (docs/planejamento/neighborhood_selection_approach.md) adota essa regra e fixa
// a ordem por complexidade computacional. Aqui medimos o CUSTO REAL de uma
// varredura completa de cada vizinhanca, para que a ordem declarada seja
// verificavel e nao apenas assumida.
TEST(neighborhood_scan_cost_ordering) {
    struct N { Neighborhood nb; const char* name; };
    const N kAll[] = {{Neighborhood::Relocate, "Relocate"}, {Neighborhood::Swap, "Swap"},
                      {Neighborhood::OrOpt, "Or-opt"}, {Neighborhood::TwoOpt, "2-opt intra"},
                      {Neighborhood::TwoOptStar, "2-opt*"},
                      {Neighborhood::CrossExchange, "Cross-exch."}};
    // solucao I1 de uma instancia representativa de cada familia
    std::cout << "  [custo de varredura] microssegundos por chamada de find_best_move\n";
    std::cout << "                       ";
    for (const char* n : {"C101", "R101", "RC101", "R201"}) std::cout << "  " << n;
    std::cout << "\n";

    for (const auto& op : kAll) {
        std::cout << "    " << op.name;
        for (int pad = static_cast<int>(std::string(op.name).size()); pad < 20; ++pad)
            std::cout << ' ';
        for (const char* name : {"C101", "R101", "RC101", "R201"}) {
            const Instance inst = parse_instance(instance_of(name).string());
            const DistanceMatrix dm(inst);
            Solution sol = solomon_i1(inst, dm);
            sol.recompute_all(inst, dm);

            const auto t0 = std::chrono::steady_clock::now();
            constexpr int kReps = 5;
            for (int r = 0; r < kReps; ++r) (void)find_best_move(sol, inst, dm, op.nb, false);
            const auto us = std::chrono::duration_cast<std::chrono::microseconds>(
                std::chrono::steady_clock::now() - t0).count() / kReps;
            std::cout << "  " << us;
            for (int pad = static_cast<int>(std::to_string(us).size()); pad < 5; ++pad)
                std::cout << ' ';
        }
        std::cout << "\n";
    }
    CHECK(true);   // medicao; a ordem declarada e verificada no documento 03
}
