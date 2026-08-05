#pragma once

#include <cstddef>
#include <functional>

#include "../core/instance.h"
#include "../core/solution.h"

namespace vrptw {

struct LocalSearchParams {
  double eps = 1e-6;
};

// ── Movimento genérico de vizinhança ──────────────────────────────────────────

struct LSMove {
  enum Type { RelocateIntra, SwapIntra, RelocateInter, OrOpt, SwapInter, TwoOptIntra, TwoOptInter, CrossExchange };
  Type type{};
  std::size_t ra = 0, rb = 0;
  std::size_t posA = 0, posB = 0;
  std::size_t segLen = 1;
  std::size_t segLenB = 1;
  int customers[8] = {-1, -1, -1, -1, -1, -1, -1, -1};
  double newCost = 0.0;
  std::size_t newRoutes = 0;
};

// Comparação lexicográfica: custo depois nº de rotas.
bool isLSImprovement(double newCost, std::size_t newRoutes, double oldCost, std::size_t oldRoutes, double eps);

// Aplica um LSMove à solução (modifica sol in-place). Retorna false se infeasível.
bool applyLSMove(Solution& sol, const Instance& inst, const LSMove& m, double eps);

// ── Enumeração de vizinhanças ────────────────────────────────────────────────
// O visitor recebe cada movimento viável. Retornar true = parar (first-improvement).

using MoveVisitor = std::function<bool(const LSMove&)>;

void enumerateRelocateIntra(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis);
void enumerateSwapIntra(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis);
void enumerateRelocateInter(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis);
void enumerateOrOpt(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis);
void enumerateSwapInter(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis);
void enumerateTwoOptIntra(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis);
void enumerateTwoOptInter(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis);
void enumerateCrossExchange(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis);

// ── Atalhos first-improvement (usados pelo VND) ─────────────────────────────

bool relocateIntraFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p);
bool swapIntraFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p);
bool relocateInterFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p);
bool orOptFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p);
bool swapInterFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p);
bool twoOptIntraFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p);
bool twoOptInterFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p);
bool crossExchangeFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p);

}  // namespace vrptw
