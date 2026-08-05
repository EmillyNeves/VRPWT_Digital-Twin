#include "vrptw/InstanceParser.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/SolutionIO.hpp"
#include "vrptw/Validator.hpp"
#include "vrptw/Evaluator.hpp"
#include <iostream>
#include <iomanip>

// Usage: validate <instance.txt> <solution.(sol|txt)>
// Re-walks the routes independently, prints feasibility, recomputed distance,
// vehicle count, and (if the file carries a Cost) whether they match.
int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "uso: " << argv[0] << " <instancia.txt> <solucao.(sol|txt)>\n";
        return 2;
    }
    using namespace vrptw;
    try {
        const Instance inst = parse_instance(argv[1]);
        const DistanceMatrix dm(inst);
        const ParsedSolution ps = read_solution_file(argv[2]);
        const Solution sol = to_solution(ps, inst, dm);
        const ValidationResult vr = validate(inst, dm, sol);

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
