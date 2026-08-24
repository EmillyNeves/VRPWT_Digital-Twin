#include "vrptw/Validator.hpp"
#include "vrptw/Route.hpp"   // kEps
#include <string>

namespace vrptw {

ValidationResult validate(const Instance& inst, const DistanceMatrix& dm, const Solution& s) {
    ValidationResult res;
    const int n = static_cast<int>(inst.size());
    std::vector<int> visits(static_cast<std::size_t>(n), 0);

    for (const auto& r : s.routes) {
        if (r.empty()) continue;
        ++res.vehicles;

        double t = inst.depot().ready;   // depart depot at time 0
        double load = 0.0;
        int prev = 0;

        for (int c : r.seq) {
            if (c <= 0 || c >= n) {
                res.errors.push_back("id de cliente invalido: " + std::to_string(c));
                continue;
            }
            ++visits[static_cast<std::size_t>(c)];

            res.distance += dm(prev, c);            // cost
            t += dm.time(prev, c);                  // arrival (time matrix; == distance by default)
            const Customer& cust = inst.node(c);
            if (t < cust.ready) {                   // wait until window opens
                res.waiting_time += cust.ready - t;
                t = cust.ready;
            }
            if (t > cust.due + kEps) {
                res.time_ok = false;
                res.errors.push_back("janela violada no cliente " + std::to_string(c));
            }
            t += cust.service;                      // departure
            res.service_time += cust.service;
            load += cust.demand;
            prev = c;
        }

        res.distance += dm(prev, 0);                // return to depot (cost)
        t += dm.time(prev, 0);                      // arrival back (time matrix)
        res.schedule_time += t - inst.depot().ready;   // route duration (departure at depot.ready)
        if (t > inst.depot().due + kEps) {
            res.returns_to_depot_ok = false;
            res.errors.push_back("retorno ao deposito apos o horizonte");
        }
        if (load > inst.capacity + kEps) {
            res.capacity_ok = false;
            res.errors.push_back("capacidade excedida (carga " + std::to_string(load) + ")");
        }
    }

    for (int i = 1; i < n; ++i) {
        if (visits[static_cast<std::size_t>(i)] != 1) {
            res.all_customers_once = false;
            res.errors.push_back("cliente " + std::to_string(i) + " visitado " +
                                 std::to_string(visits[static_cast<std::size_t>(i)]) + "x (esperado 1)");
        }
    }

    // Regra DIMACS: a solucao FINAL deve respeitar o numero maximo de veiculos
    // declarado na instancia (nao ha bonus por usar menos). inst.vehicles == 0
    // significa "sem limite declarado". fleet_ok fica FORA de `feasible` (as
    // quatro restricoes do VRPTW) porque estados intermediarios de diagnostico
    // podem exceder a frota; o portao final do binario (apps/solve.cpp) exige
    // feasible && fleet_ok.
    if (inst.vehicles > 0 && res.vehicles > inst.vehicles) {
        res.fleet_ok = false;
        res.errors.push_back("frota excedida: " + std::to_string(res.vehicles) +
                             " veiculos (maximo " + std::to_string(inst.vehicles) + ")");
    }

    res.feasible = res.all_customers_once && res.capacity_ok &&
                   res.time_ok && res.returns_to_depot_ok;
    return res;
}

} // namespace vrptw
