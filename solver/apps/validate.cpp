#include "vrptw/InstanceParser.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/SolutionIO.hpp"
#include "vrptw/Validator.hpp"
#include "vrptw/Evaluator.hpp"
#include <iostream>
#include <iomanip>

// Usage: validate <instance.txt> <solution.(sol|txt)> [--csv]
// Re-walks the routes independently, prints feasibility, recomputed distance,
// vehicle count, and (if the file carries a Cost) whether they match.
//
// --csv emite UMA LINHA POR ROTA com a folga efetiva de cada restricao: quanto
// sobrou de capacidade, quao perto a janela mais apertada chegou de ser violada,
// e quanto sobrou do horizonte no retorno ao deposito. E a evidencia de que as
// rotas respeitam janelas e capacidade -- o booleano `feasible` sozinho nao
// mostra a margem, e margem zero e o que separa uma solucao valida de uma
// invalida por erro de arredondamento.
int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "uso: " << argv[0] << " <instancia.txt> <solucao.(sol|txt)> [--csv]\n";
        return 2;
    }
    using namespace vrptw;
    const bool csv = (argc > 3 && std::string(argv[3]) == "--csv");
    try {
        const Instance inst = parse_instance(argv[1]);
        const DistanceMatrix dm(inst);
        const ParsedSolution ps = read_solution_file(argv[2]);
        const Solution sol = to_solution(ps, inst, dm);
        const ValidationResult vr = validate(inst, dm, sol);

        if (csv) {
            // instancia,rota,clientes,carga,capacidade,folga_carga,dist,
            // retorno,horizonte,folga_horizonte,folga_janela_min,cliente_critico,viavel
            int k = 0;
            for (const auto& r : sol.routes) {
                if (r.empty()) continue;
                ++k;
                double t = inst.depot().ready, load = 0.0, dist = 0.0;
                double min_slack = 1e300;
                int tight = -1;
                int prev = 0;
                for (int c : r.seq) {
                    dist += dm(prev, c);
                    t += dm.time(prev, c);
                    const Customer& cu = inst.node(c);
                    if (t < cu.ready) t = cu.ready;          // espera
                    const double slack = cu.due - t;          // folga da janela
                    if (slack < min_slack) { min_slack = slack; tight = c; }
                    t += cu.service;
                    load += cu.demand;
                    prev = c;
                }
                dist += dm(prev, 0);
                t += dm.time(prev, 0);
                const bool ok = (load <= inst.capacity + 1e-6) && (min_slack >= -1e-6) &&
                                (t <= inst.depot().due + 1e-6);
                std::cout << inst.name << ',' << k << ',' << r.seq.size() << ','
                          << std::fixed << std::setprecision(2)
                          << load << ',' << inst.capacity << ',' << (inst.capacity - load) << ','
                          << std::setprecision(1) << dist << ','
                          << t << ',' << inst.depot().due << ',' << (inst.depot().due - t) << ','
                          << min_slack << ',' << tight << ',' << (ok ? 1 : 0) << '\n';
            }
            return vr.feasible ? 0 : 1;
        }

        std::cout << std::fixed << std::setprecision(2);
        std::cout << "instancia      : " << inst.name
                  << "  (clientes=" << inst.num_customers()
                  << ", Q=" << inst.capacity << ")\n";
        std::cout << "viavel         : " << (vr.feasible ? "sim" : "NAO") << '\n';
        std::cout << "  cobertura    : " << (vr.all_customers_once ? "ok" : "FALHA") << '\n';
        std::cout << "  capacidade   : " << (vr.capacity_ok ? "ok" : "FALHA") << '\n';
        std::cout << "  janelas      : " << (vr.time_ok ? "ok" : "FALHA") << '\n';
        std::cout << "  retorno dep. : " << (vr.returns_to_depot_ok ? "ok" : "FALHA") << '\n';
        std::cout << "veiculos       : " << vr.vehicles << '\n';
        std::cout << "distancia      : " << Evaluator::round1(vr.distance) << " (1 casa)\n";
        if (ps.cost) {
            const double diff = Evaluator::round1(vr.distance) - *ps.cost;
            std::cout << "custo do arq.  : " << *ps.cost
                      << "  (diferenca = " << diff << ")\n";
        }
        for (const auto& e : vr.errors) std::cout << "  ! " << e << '\n';
        return vr.feasible ? 0 : 1;
    } catch (const std::exception& e) {
        std::cerr << "erro: " << e.what() << '\n';
        return 2;
    }
}
