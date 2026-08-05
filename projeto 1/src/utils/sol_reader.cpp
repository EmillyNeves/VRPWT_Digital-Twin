#include "sol_reader.h"

#include <cctype>
#include <fstream>
#include <sstream>
#include <string>

#include "../core/route.h"
#include "../core/solution.h"

namespace vrptw {

static std::string trim(const std::string& s) {
  std::size_t start = 0;
  while (start < s.size() && std::isspace(static_cast<unsigned char>(s[start]))) ++start;
  std::size_t end = s.size();
  while (end > start && std::isspace(static_cast<unsigned char>(s[end - 1]))) --end;
  return s.substr(start, end - start);
}

static bool fail(std::string* error, const std::string& msg) {
  if (error) *error = msg;
  return false;
}

bool readSol(const std::string& path, Solution* out, std::string* error) {
  if (!out) return fail(error, "Destino nulo");
  *out = Solution{};

  std::ifstream in(path);
  if (!in) return fail(error, "Falha ao abrir: " + path);

  std::string line;
  bool anyRoute = false;

  while (std::getline(in, line)) {
    line = trim(line);
    if (line.empty()) continue;

    if (line.rfind("Route", 0) == 0) {
      const auto pos = line.find(':');
      if (pos == std::string::npos) return fail(error, "Linha Route sem ':'");

      std::istringstream iss(line.substr(pos + 1));
      Route r;
      r.seq.push_back(0);
      int id = 0;
      while (iss >> id) {
        if (id == 0) continue;
        r.seq.push_back(id);
      }
      r.seq.push_back(0);
      out->routes.push_back(std::move(r));
      anyRoute = true;
      continue;
    }

    if (line.rfind("Cost", 0) == 0) {
      // Ignore cost, recomputed later.
      continue;
    }
  }

  if (!anyRoute) return fail(error, "Nenhuma rota encontrada em: " + path);
  return true;
}

}  // namespace vrptw

