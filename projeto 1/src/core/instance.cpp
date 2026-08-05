#include "instance.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>

namespace vrptw {

static std::string trim(const std::string& s) {
  std::size_t start = 0;
  while (start < s.size() && std::isspace(static_cast<unsigned char>(s[start]))) ++start;
  std::size_t end = s.size();
  while (end > start && std::isspace(static_cast<unsigned char>(s[end - 1]))) --end;
  return s.substr(start, end - start);
}

static void computeDistances(Instance& inst) {
  const std::size_t n = inst.customers.size();
  inst.dist.assign(n, std::vector<double>(n, 0.0));
  for (std::size_t i = 0; i < n; ++i) {
    for (std::size_t j = i + 1; j < n; ++j) {
      const double dx = inst.customers[i].x - inst.customers[j].x;
      const double dy = inst.customers[i].y - inst.customers[j].y;
      // Solomon: travel time / distance is Euclidean, truncated to 1 decimal place (floor).
      // This matches the common BKS cost convention used in the provided `solution/*.sol`.
      const double d = std::hypot(dx, dy);
      const double d1 = std::floor(d * 10.0 + 1e-9) / 10.0;
      inst.dist[i][j] = d1;
      inst.dist[j][i] = d1;
    }
  }
}

static void computeNearest(Instance& inst, std::size_t k) {
  const std::size_t n = inst.customers.size();
  inst.nearest.assign(n, {});
  inst.nearestSet.assign(n, {});
  inst.kNeighbors = k;

  for (std::size_t i = 0; i < n; ++i) {
    std::vector<std::pair<double, int>> v;
    v.reserve(n > 0 ? n - 1 : 0);
    for (std::size_t j = 0; j < n; ++j) {
      if (i == j) continue;
      v.emplace_back(inst.dist[i][j], static_cast<int>(j));
    }
    std::sort(v.begin(), v.end(), [](const auto& a, const auto& b) { return a.first < b.first; });
    const std::size_t kk = std::min(k, v.size());
    inst.nearest[i].reserve(kk);
    inst.nearestSet[i].reserve(kk * 2);
    for (std::size_t t = 0; t < kk; ++t) {
      inst.nearest[i].push_back(v[t].second);
      inst.nearestSet[i].insert(v[t].second);
    }
  }
}

Instance Instance::readSolomon(const std::string& path, std::size_t kNeighbors) {
  std::ifstream in(path);
  if (!in) throw std::runtime_error("Falha ao abrir instancia: " + path);

  Instance inst;
  std::string line;

  if (!std::getline(in, line)) throw std::runtime_error("Arquivo vazio: " + path);
  inst.name = trim(line);
  if (!inst.name.empty() && inst.name.back() == '\r') inst.name.pop_back();

  bool foundCapacity = false;
  while (std::getline(in, line)) {
    if (line.find("NUMBER") != std::string::npos && line.find("CAPACITY") != std::string::npos) {
      while (std::getline(in, line)) {
        std::istringstream iss(line);
        int v = 0, q = 0;
        if (iss >> v >> q) {
          inst.vehicleCount = v;
          inst.capacity = q;
          foundCapacity = true;
          break;
        }
      }
      break;
    }
  }
  if (!foundCapacity) throw std::runtime_error("Nao encontrou NUMBER/CAPACITY em: " + path);

  bool foundCustomerHeader = false;
  while (std::getline(in, line)) {
    if (line.find("CUST") != std::string::npos && line.find("READY") != std::string::npos) {
      foundCustomerHeader = true;
      break;
    }
  }
  if (!foundCustomerHeader) throw std::runtime_error("Nao encontrou cabecalho CUSTOMER em: " + path);

  inst.customers.clear();
  while (std::getline(in, line)) {
    if (line.empty()) continue;
    std::istringstream iss(line);
    int id = -1;
    double x = 0.0, y = 0.0;
    int demand = 0;
    double ready = 0.0, due = 0.0, service = 0.0;
    if (!(iss >> id >> x >> y >> demand >> ready >> due >> service)) continue;
    if (id < 0) continue;

    if (static_cast<std::size_t>(id) >= inst.customers.size()) inst.customers.resize(static_cast<std::size_t>(id) + 1);
    Customer c;
    c.id = id;
    c.x = x;
    c.y = y;
    c.demand = demand;
    c.ready = ready;
    c.due = due;
    c.service = service;
    inst.customers[static_cast<std::size_t>(id)] = c;
  }

  if (inst.customers.empty() || inst.customers[0].id != 0) {
    throw std::runtime_error("Instancia invalida (sem deposito id=0): " + path);
  }

  computeDistances(inst);
  computeNearest(inst, kNeighbors);
  return inst;
}

bool Instance::isNeighborOrDepot(int a, int b) const {
  if (a == 0 || b == 0) return true;
  if (a < 0 || b < 0) return false;
  const std::size_t ia = static_cast<std::size_t>(a);
  if (ia >= nearestSet.size()) return false;
  return nearestSet[ia].contains(b);
}

}  // namespace vrptw
