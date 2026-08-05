#include "local_search.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <vector>

namespace vrptw {

// ── Utilidades ───────────────────────────────────────────────────────────────

bool isLSImprovement(double newCost, std::size_t newRoutes, double oldCost, std::size_t oldRoutes, double eps) {
  if (newCost < oldCost - eps) return true;
  if (std::fabs(newCost - oldCost) <= eps && newRoutes < oldRoutes) return true;
  return false;
}

// ── applyLSMove ──────────────────────────────────────────────────────────────

bool applyLSMove(Solution& sol, const Instance& inst, const LSMove& m, double eps) {
  switch (m.type) {
    case LSMove::RelocateIntra: {
      Route& a = sol.routes[m.ra];
      const int u = a.seq[m.posA];
      a.seq.erase(a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA));
      std::size_t ins = m.posB;
      if (m.posB > m.posA) ins = m.posB - 1;
      a.seq.insert(a.seq.begin() + static_cast<std::ptrdiff_t>(ins), u);
      break;
    }
    case LSMove::SwapIntra: {
      Route& a = sol.routes[m.ra];
      std::swap(a.seq[m.posA], a.seq[m.posB]);
      break;
    }
    case LSMove::RelocateInter: {
      Route& a = sol.routes[m.ra];
      Route& b = sol.routes[m.rb];
      const int u = a.seq[m.posA];
      a.seq.erase(a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA));
      b.seq.insert(b.seq.begin() + static_cast<std::ptrdiff_t>(m.posB), u);
      break;
    }
    case LSMove::OrOpt: {
      Route& a = sol.routes[m.ra];
      if (m.ra == m.rb) {
        std::vector<int> seg(a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA),
                             a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA + m.segLen));
        a.seq.erase(a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA),
                     a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA + m.segLen));
        std::size_t ins = m.posB;
        if (m.posB > m.posA) ins = m.posB - m.segLen;
        a.seq.insert(a.seq.begin() + static_cast<std::ptrdiff_t>(ins), seg.begin(), seg.end());
      } else {
        Route& b = sol.routes[m.rb];
        std::vector<int> seg(a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA),
                             a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA + m.segLen));
        a.seq.erase(a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA),
                     a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA + m.segLen));
        b.seq.insert(b.seq.begin() + static_cast<std::ptrdiff_t>(m.posB), seg.begin(), seg.end());
      }
      break;
    }
    case LSMove::SwapInter: {
      Route& a = sol.routes[m.ra];
      Route& b = sol.routes[m.rb];
      std::swap(a.seq[m.posA], b.seq[m.posB]);
      break;
    }
    case LSMove::TwoOptIntra: {
      Route& a = sol.routes[m.ra];
      std::reverse(a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA),
                   a.seq.begin() + static_cast<std::ptrdiff_t>(m.posB + 1));
      break;
    }
    case LSMove::TwoOptInter: {
      Route& a = sol.routes[m.ra];
      Route& b = sol.routes[m.rb];
      const std::vector<int> oldA = a.seq;
      const std::vector<int> oldB = b.seq;

      std::vector<int> newA;
      std::vector<int> newB;
      newA.reserve((m.posA + 1) + (oldB.size() - (m.posB + 1)));
      newB.reserve((m.posB + 1) + (oldA.size() - (m.posA + 1)));

      newA.insert(newA.end(), oldA.begin(), oldA.begin() + static_cast<std::ptrdiff_t>(m.posA + 1));
      newA.insert(newA.end(), oldB.begin() + static_cast<std::ptrdiff_t>(m.posB + 1), oldB.end());

      newB.insert(newB.end(), oldB.begin(), oldB.begin() + static_cast<std::ptrdiff_t>(m.posB + 1));
      newB.insert(newB.end(), oldA.begin() + static_cast<std::ptrdiff_t>(m.posA + 1), oldA.end());

      a.seq = std::move(newA);
      b.seq = std::move(newB);
      break;
    }
    case LSMove::CrossExchange: {
      Route& a = sol.routes[m.ra];
      Route& b = sol.routes[m.rb];

      std::vector<int> segA(a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA),
                            a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA + m.segLen));
      std::vector<int> segB(b.seq.begin() + static_cast<std::ptrdiff_t>(m.posB),
                            b.seq.begin() + static_cast<std::ptrdiff_t>(m.posB + m.segLenB));

      a.seq.erase(a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA),
                  a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA + m.segLen));
      b.seq.erase(b.seq.begin() + static_cast<std::ptrdiff_t>(m.posB),
                  b.seq.begin() + static_cast<std::ptrdiff_t>(m.posB + m.segLenB));

      a.seq.insert(a.seq.begin() + static_cast<std::ptrdiff_t>(m.posA), segB.begin(), segB.end());
      b.seq.insert(b.seq.begin() + static_cast<std::ptrdiff_t>(m.posB), segA.begin(), segA.end());
      break;
    }
  }
  return sol.recompute(inst, eps);
}

// ── Enumeração: RelocateIntra ────────────────────────────────────────────────

void enumerateRelocateIntra(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis) {
  for (std::size_t rIdx = 0; rIdx < sol.routes.size(); ++rIdx) {
    const Route& r0 = sol.routes[rIdx];
    if (r0.seq.size() <= 3) continue;
    for (std::size_t i = 1; i + 1 < r0.seq.size(); ++i) {
      const int u = r0.seq[i];
      for (std::size_t j = 1; j < r0.seq.size(); ++j) {
        if (j == i || j == i + 1) continue;

        Route cand = r0;
        cand.seq.erase(cand.seq.begin() + static_cast<std::ptrdiff_t>(i));
        std::size_t insertPos = j;
        if (j > i) insertPos = j - 1;
        cand.seq.insert(cand.seq.begin() + static_cast<std::ptrdiff_t>(insertPos), u);

        if (!cand.recompute(inst, eps)) continue;
        const double newCost = sol.cost - r0.cost + cand.cost;

        LSMove m{};
        m.type = LSMove::RelocateIntra;
        m.ra = rIdx;
        m.rb = rIdx;
        m.posA = i;
        m.posB = j;
        m.customers[0] = u;
        m.newCost = newCost;
        m.newRoutes = sol.routes.size();

        if (vis(m)) return;
      }
    }
  }
}

// ── Enumeração: SwapIntra ────────────────────────────────────────────────────

void enumerateSwapIntra(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis) {
  for (std::size_t rIdx = 0; rIdx < sol.routes.size(); ++rIdx) {
    const Route& r0 = sol.routes[rIdx];
    if (r0.seq.size() <= 4) continue;
    for (std::size_t i = 1; i + 2 < r0.seq.size(); ++i) {
      for (std::size_t j = i + 1; j + 1 < r0.seq.size(); ++j) {
        Route cand = r0;
        std::swap(cand.seq[i], cand.seq[j]);
        if (!cand.recompute(inst, eps)) continue;
        const double newCost = sol.cost - r0.cost + cand.cost;

        LSMove m{};
        m.type = LSMove::SwapIntra;
        m.ra = rIdx;
        m.rb = rIdx;
        m.posA = i;
        m.posB = j;
        m.customers[0] = r0.seq[i];
        m.customers[1] = r0.seq[j];
        m.newCost = newCost;
        m.newRoutes = sol.routes.size();

        if (vis(m)) return;
      }
    }
  }
}

// ── Enumeração: RelocateInter ────────────────────────────────────────────────

void enumerateRelocateInter(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis) {
  if (sol.routes.size() < 2) return;

  for (std::size_t ra = 0; ra < sol.routes.size(); ++ra) {
    const Route& a0 = sol.routes[ra];
    if (a0.seq.size() <= 3) continue;

    for (std::size_t i = 1; i + 1 < a0.seq.size(); ++i) {
      const int u = a0.seq[i];
      for (std::size_t rb = 0; rb < sol.routes.size(); ++rb) {
        if (rb == ra) continue;
        const Route& b0 = sol.routes[rb];

        for (std::size_t j = 1; j < b0.seq.size(); ++j) {
          Route a = a0;
          Route b = b0;
          a.seq.erase(a.seq.begin() + static_cast<std::ptrdiff_t>(i));
          b.seq.insert(b.seq.begin() + static_cast<std::ptrdiff_t>(j), u);

          if (!a.recompute(inst, eps)) continue;
          if (!b.recompute(inst, eps)) continue;

          const double newCost = sol.cost - a0.cost - b0.cost + a.cost + b.cost;
          const std::size_t newRoutes = sol.routes.size() - (a.isTrivial() ? 1U : 0U);

          LSMove m{};
          m.type = LSMove::RelocateInter;
          m.ra = ra;
          m.rb = rb;
          m.posA = i;
          m.posB = j;
          m.customers[0] = u;
          m.newCost = newCost;
          m.newRoutes = newRoutes;

          if (vis(m)) return;
        }
      }
    }
  }
}

// ── Enumeração: OrOpt ────────────────────────────────────────────────────────

void enumerateOrOpt(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis) {
  if (sol.routes.empty()) return;

  for (std::size_t ra = 0; ra < sol.routes.size(); ++ra) {
    const Route& a0 = sol.routes[ra];
    if (a0.seq.size() <= 3) continue;

    for (std::size_t segLen = 2; segLen <= 3; ++segLen) {
      for (std::size_t i = 1; i + segLen < a0.seq.size(); ++i) {
        for (std::size_t rb = 0; rb < sol.routes.size(); ++rb) {
          const Route& b0 = sol.routes[rb];
          for (std::size_t insertPos = 1; insertPos < b0.seq.size(); ++insertPos) {
            if (ra == rb) {
              if (insertPos >= i && insertPos <= i + segLen) continue;

              Route cand = a0;
              std::vector<int> seg(cand.seq.begin() + static_cast<std::ptrdiff_t>(i),
                                   cand.seq.begin() + static_cast<std::ptrdiff_t>(i + segLen));
              cand.seq.erase(cand.seq.begin() + static_cast<std::ptrdiff_t>(i),
                             cand.seq.begin() + static_cast<std::ptrdiff_t>(i + segLen));
              std::size_t ins = insertPos;
              if (insertPos > i) ins = insertPos - segLen;
              cand.seq.insert(cand.seq.begin() + static_cast<std::ptrdiff_t>(ins), seg.begin(), seg.end());

              if (!cand.recompute(inst, eps)) continue;
              const double newCost = sol.cost - a0.cost + cand.cost;

              LSMove m{};
              m.type = LSMove::OrOpt;
              m.ra = ra;
              m.rb = ra;
              m.posA = i;
              m.posB = insertPos;
              m.segLen = segLen;
              m.customers[0] = a0.seq[i];
              if (segLen >= 2) m.customers[1] = a0.seq[i + 1];
              if (segLen >= 3) m.customers[2] = a0.seq[i + 2];
              m.newCost = newCost;
              m.newRoutes = sol.routes.size();

              if (vis(m)) return;
            } else {
              if (insertPos == 0 || insertPos >= b0.seq.size()) continue;

              Route a = a0;
              Route b = b0;
              std::vector<int> seg(a.seq.begin() + static_cast<std::ptrdiff_t>(i),
                                   a.seq.begin() + static_cast<std::ptrdiff_t>(i + segLen));
              a.seq.erase(a.seq.begin() + static_cast<std::ptrdiff_t>(i),
                          a.seq.begin() + static_cast<std::ptrdiff_t>(i + segLen));
              b.seq.insert(b.seq.begin() + static_cast<std::ptrdiff_t>(insertPos), seg.begin(), seg.end());

              if (!a.recompute(inst, eps)) continue;
              if (!b.recompute(inst, eps)) continue;

              const double newCost = sol.cost - a0.cost - b0.cost + a.cost + b.cost;
              const std::size_t newRoutes = sol.routes.size() - (a.isTrivial() ? 1U : 0U);

              LSMove m{};
              m.type = LSMove::OrOpt;
              m.ra = ra;
              m.rb = rb;
              m.posA = i;
              m.posB = insertPos;
              m.segLen = segLen;
              m.customers[0] = a0.seq[i];
              if (segLen >= 2) m.customers[1] = a0.seq[i + 1];
              if (segLen >= 3) m.customers[2] = a0.seq[i + 2];
              m.newCost = newCost;
              m.newRoutes = newRoutes;

              if (vis(m)) return;
            }
          }
        }
      }
    }
  }
}

// ── Enumeração: SwapInter ─────────────────────────────────────────────────────

void enumerateSwapInter(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis) {
  if (sol.routes.size() < 2) return;

  for (std::size_t ra = 0; ra < sol.routes.size(); ++ra) {
    const Route& a0 = sol.routes[ra];
    if (a0.seq.size() <= 2) continue;

    for (std::size_t rb = ra + 1; rb < sol.routes.size(); ++rb) {
      const Route& b0 = sol.routes[rb];
      if (b0.seq.size() <= 2) continue;

      for (std::size_t i = 1; i + 1 < a0.seq.size(); ++i) {
        for (std::size_t j = 1; j + 1 < b0.seq.size(); ++j) {
          Route a = a0;
          Route b = b0;
          std::swap(a.seq[i], b.seq[j]);

          if (!a.recompute(inst, eps)) continue;
          if (!b.recompute(inst, eps)) continue;

          const double newCost = sol.cost - a0.cost - b0.cost + a.cost + b.cost;

          LSMove m{};
          m.type = LSMove::SwapInter;
          m.ra = ra;
          m.rb = rb;
          m.posA = i;
          m.posB = j;
          m.customers[0] = a0.seq[i];
          m.customers[1] = b0.seq[j];
          m.newCost = newCost;
          m.newRoutes = sol.routes.size();

          if (vis(m)) return;
        }
      }
    }
  }
}

// ── Enumeração: TwoOptIntra ───────────────────────────────────────────────────

void enumerateTwoOptIntra(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis) {
  for (std::size_t rIdx = 0; rIdx < sol.routes.size(); ++rIdx) {
    const Route& r0 = sol.routes[rIdx];
    if (r0.seq.size() <= 3) continue;

    for (std::size_t i = 1; i + 2 < r0.seq.size(); ++i) {
      for (std::size_t j = i + 1; j + 1 < r0.seq.size(); ++j) {
        Route cand = r0;
        std::reverse(cand.seq.begin() + static_cast<std::ptrdiff_t>(i),
                     cand.seq.begin() + static_cast<std::ptrdiff_t>(j + 1));
        if (!cand.recompute(inst, eps)) continue;
        const double newCost = sol.cost - r0.cost + cand.cost;

        LSMove m{};
        m.type = LSMove::TwoOptIntra;
        m.ra = rIdx;
        m.rb = rIdx;
        m.posA = i;
        m.posB = j;
        m.customers[0] = r0.seq[i];
        m.customers[1] = r0.seq[j];
        m.newCost = newCost;
        m.newRoutes = sol.routes.size();

        if (vis(m)) return;
      }
    }
  }
}

// ── Enumeração: TwoOptInter (aka TwoOptStarInter) ────────────────────────────

void enumerateTwoOptInter(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis) {
  if (sol.routes.size() < 2) return;

  for (std::size_t ra = 0; ra < sol.routes.size(); ++ra) {
    const Route& a0 = sol.routes[ra];
    for (std::size_t rb = ra + 1; rb < sol.routes.size(); ++rb) {
      const Route& b0 = sol.routes[rb];

      for (std::size_t cutA = 0; cutA + 1 < a0.seq.size(); ++cutA) {
        for (std::size_t cutB = 0; cutB + 1 < b0.seq.size(); ++cutB) {
          if (cutA == a0.seq.size() - 2 && cutB == b0.seq.size() - 2) continue;

          Route a;
          Route b;

          a.seq.reserve((cutA + 1) + (b0.seq.size() - (cutB + 1)));
          b.seq.reserve((cutB + 1) + (a0.seq.size() - (cutA + 1)));

          a.seq.insert(a.seq.end(), a0.seq.begin(), a0.seq.begin() + static_cast<std::ptrdiff_t>(cutA + 1));
          a.seq.insert(a.seq.end(), b0.seq.begin() + static_cast<std::ptrdiff_t>(cutB + 1), b0.seq.end());

          b.seq.insert(b.seq.end(), b0.seq.begin(), b0.seq.begin() + static_cast<std::ptrdiff_t>(cutB + 1));
          b.seq.insert(b.seq.end(), a0.seq.begin() + static_cast<std::ptrdiff_t>(cutA + 1), a0.seq.end());

          if (!a.recompute(inst, eps)) continue;
          if (!b.recompute(inst, eps)) continue;

          const double newCost = sol.cost - a0.cost - b0.cost + a.cost + b.cost;
          const std::size_t newRoutes =
              sol.routes.size() - (a.isTrivial() ? 1U : 0U) - (b.isTrivial() ? 1U : 0U);

          LSMove m{};
          m.type = LSMove::TwoOptInter;
          m.ra = ra;
          m.rb = rb;
          m.posA = cutA;
          m.posB = cutB;
          m.customers[0] = a0.seq[cutA];
          m.customers[1] = a0.seq[cutA + 1];
          m.customers[2] = b0.seq[cutB];
          m.customers[3] = b0.seq[cutB + 1];
          m.newCost = newCost;
          m.newRoutes = newRoutes;

          if (vis(m)) return;
        }
      }
    }
  }
}

// ── Enumeração: CrossExchange ─────────────────────────────────────────────────

void enumerateCrossExchange(const Solution& sol, const Instance& inst, double eps, const MoveVisitor& vis) {
  if (sol.routes.size() < 2) return;

  for (std::size_t ra = 0; ra < sol.routes.size(); ++ra) {
    const Route& a0 = sol.routes[ra];
    if (a0.seq.size() <= 2) continue;

    for (std::size_t rb = ra + 1; rb < sol.routes.size(); ++rb) {
      const Route& b0 = sol.routes[rb];
      if (b0.seq.size() <= 2) continue;

      for (std::size_t lenA = 1; lenA <= 2; ++lenA) {
        if (a0.seq.size() < lenA + 2) continue;
        for (std::size_t lenB = 1; lenB <= 2; ++lenB) {
          if (b0.seq.size() < lenB + 2) continue;

          for (std::size_t i = 1; i + lenA < a0.seq.size(); ++i) {
            for (std::size_t j = 1; j + lenB < b0.seq.size(); ++j) {
              Route a = a0;
              Route b = b0;

              std::vector<int> segA(a.seq.begin() + static_cast<std::ptrdiff_t>(i),
                                    a.seq.begin() + static_cast<std::ptrdiff_t>(i + lenA));
              std::vector<int> segB(b.seq.begin() + static_cast<std::ptrdiff_t>(j),
                                    b.seq.begin() + static_cast<std::ptrdiff_t>(j + lenB));

              a.seq.erase(a.seq.begin() + static_cast<std::ptrdiff_t>(i),
                          a.seq.begin() + static_cast<std::ptrdiff_t>(i + lenA));
              b.seq.erase(b.seq.begin() + static_cast<std::ptrdiff_t>(j),
                          b.seq.begin() + static_cast<std::ptrdiff_t>(j + lenB));

              a.seq.insert(a.seq.begin() + static_cast<std::ptrdiff_t>(i), segB.begin(), segB.end());
              b.seq.insert(b.seq.begin() + static_cast<std::ptrdiff_t>(j), segA.begin(), segA.end());

              if (!a.recompute(inst, eps)) continue;
              if (!b.recompute(inst, eps)) continue;

              const double newCost = sol.cost - a0.cost - b0.cost + a.cost + b.cost;
              const std::size_t newRoutes =
                  sol.routes.size() - (a.isTrivial() ? 1U : 0U) - (b.isTrivial() ? 1U : 0U);

              LSMove m{};
              m.type = LSMove::CrossExchange;
              m.ra = ra;
              m.rb = rb;
              m.posA = i;
              m.posB = j;
              m.segLen = lenA;
              m.segLenB = lenB;
              int cidx = 0;
              for (std::size_t k = 0; k < lenA; ++k) m.customers[cidx++] = a0.seq[i + k];
              for (std::size_t k = 0; k < lenB; ++k) m.customers[cidx++] = b0.seq[j + k];
              m.newCost = newCost;
              m.newRoutes = newRoutes;

              if (vis(m)) return;
            }
          }
        }
      }
    }
  }
}

// ── First-improvement (usados pelo VND) ──────────────────────────────────────

bool relocateIntraFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p) {
  bool improved = false;
  enumerateRelocateIntra(sol, inst, p.eps, [&](const LSMove& m) -> bool {
    if (isLSImprovement(m.newCost, m.newRoutes, sol.cost, sol.numRoutes(), p.eps)) {
      applyLSMove(sol, inst, m, p.eps);
      improved = true;
      return true;
    }
    return false;
  });
  return improved;
}

bool swapIntraFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p) {
  bool improved = false;
  enumerateSwapIntra(sol, inst, p.eps, [&](const LSMove& m) -> bool {
    if (isLSImprovement(m.newCost, m.newRoutes, sol.cost, sol.numRoutes(), p.eps)) {
      applyLSMove(sol, inst, m, p.eps);
      improved = true;
      return true;
    }
    return false;
  });
  return improved;
}

bool relocateInterFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p) {
  bool improved = false;
  enumerateRelocateInter(sol, inst, p.eps, [&](const LSMove& m) -> bool {
    if (isLSImprovement(m.newCost, m.newRoutes, sol.cost, sol.numRoutes(), p.eps)) {
      applyLSMove(sol, inst, m, p.eps);
      improved = true;
      return true;
    }
    return false;
  });
  return improved;
}

bool orOptFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p) {
  bool improved = false;
  enumerateOrOpt(sol, inst, p.eps, [&](const LSMove& m) -> bool {
    if (isLSImprovement(m.newCost, m.newRoutes, sol.cost, sol.numRoutes(), p.eps)) {
      applyLSMove(sol, inst, m, p.eps);
      improved = true;
      return true;
    }
    return false;
  });
  return improved;
}

bool swapInterFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p) {
  bool improved = false;
  enumerateSwapInter(sol, inst, p.eps, [&](const LSMove& m) -> bool {
    if (isLSImprovement(m.newCost, m.newRoutes, sol.cost, sol.numRoutes(), p.eps)) {
      applyLSMove(sol, inst, m, p.eps);
      improved = true;
      return true;
    }
    return false;
  });
  return improved;
}

bool twoOptIntraFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p) {
  bool improved = false;
  enumerateTwoOptIntra(sol, inst, p.eps, [&](const LSMove& m) -> bool {
    if (isLSImprovement(m.newCost, m.newRoutes, sol.cost, sol.numRoutes(), p.eps)) {
      applyLSMove(sol, inst, m, p.eps);
      improved = true;
      return true;
    }
    return false;
  });
  return improved;
}

bool twoOptInterFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p) {
  bool improved = false;
  enumerateTwoOptInter(sol, inst, p.eps, [&](const LSMove& m) -> bool {
    if (isLSImprovement(m.newCost, m.newRoutes, sol.cost, sol.numRoutes(), p.eps)) {
      applyLSMove(sol, inst, m, p.eps);
      improved = true;
      return true;
    }
    return false;
  });
  return improved;
}

bool crossExchangeFirst(Solution& sol, const Instance& inst, const LocalSearchParams& p) {
  bool improved = false;
  enumerateCrossExchange(sol, inst, p.eps, [&](const LSMove& m) -> bool {
    if (isLSImprovement(m.newCost, m.newRoutes, sol.cost, sol.numRoutes(), p.eps)) {
      applyLSMove(sol, inst, m, p.eps);
      improved = true;
      return true;
    }
    return false;
  });
  return improved;
}

}  // namespace vrptw
