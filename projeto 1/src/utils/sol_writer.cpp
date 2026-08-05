#include "sol_writer.h"

#include <fstream>
#include <iomanip>
#include <stdexcept>

#include "../core/solution.h"

namespace vrptw {

void writeSol(const Solution& sol, const std::string& path, int precision) {
  std::ofstream out(path);
  if (!out) throw std::runtime_error("Falha ao escrever: " + path);

  for (std::size_t r = 0; r < sol.routes.size(); ++r) {
    out << "Route #" << (r + 1) << ": ";
    const auto& seq = sol.routes[r].seq;
    for (std::size_t i = 1; i + 1 < seq.size(); ++i) {
      out << seq[i] << ' ';
    }
    out << "\n";
  }
  out << "Cost " << std::fixed << std::setprecision(precision) << sol.cost << "\n";
}

}  // namespace vrptw

