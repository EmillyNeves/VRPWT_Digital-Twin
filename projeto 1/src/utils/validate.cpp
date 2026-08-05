#include "validate.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <sstream>
#include <vector>

#include "../core/instance.h"
#include "../core/solution.h"

namespace vrptw {

static bool fail(std::string* error, const std::string& msg) {
  if (error) *error = msg;
  return false;
}

bool validateSolution(Solution& sol, const Instance& inst, double eps, std::string* error) {
  // Remove trivial routes early.
  sol.routes.erase(std::remove_if(sol.routes.begin(), sol.routes.end(), [](const Route& r) { return r.isTrivial(); }),
                   sol.routes.end());

  if (static_cast<int>(sol.routes.size()) > inst.vehicleCount) {
    return fail(error, "Solucao excede numero maximo de veiculos (rotas=" + std::to_string(sol.routes.size()) +
                           ", V=" + std::to_string(inst.vehicleCount) + ")");
  }

  const std::size_t n = inst.customers.size();
  std::vector<int> seen(n, 0);

  double totalCost = 0.0;
  for (std::size_t rIdx = 0; rIdx < sol.routes.size(); ++rIdx) {
    Route& r = sol.routes[rIdx];
    if (r.seq.size() < 2) return fail(error, "Rota invalida (tamanho) em #" + std::to_string(rIdx + 1));
    if (r.seq.front() != 0 || r.seq.back() != 0) {
      return fail(error, "Rota nao comeca/termina no deposito em #" + std::to_string(rIdx + 1));
    }

    for (std::size_t i = 1; i + 1 < r.seq.size(); ++i) {
      const int c = r.seq[i];
      if (c <= 0 || static_cast<std::size_t>(c) >= n) {
        return fail(error, "Cliente invalido (" + std::to_string(c) + ") em #" + std::to_string(rIdx + 1));
      }
      if (++seen[static_cast<std::size_t>(c)] > 1) {
        return fail(error, "Cliente repetido (" + std::to_string(c) + ")");
      }
    }

    if (!r.recompute(inst, eps)) {
      return fail(error, "Rota infeasible (capacidade/janela) em #" + std::to_string(rIdx + 1));
    }
    totalCost += r.cost;
  }

  for (std::size_t c = 1; c < n; ++c) {
    if (seen[c] != 1) {
      return fail(error, "Cliente ausente (" + std::to_string(static_cast<int>(c)) + ")");
    }
  }

  // Limpa lixo de precisão IEEE 754 acumulado na soma de doubles.
  totalCost = std::round(totalCost * 10.0) / 10.0;

  sol.cost = totalCost;
  return true;
}

}  // namespace vrptw

