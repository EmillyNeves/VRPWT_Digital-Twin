#pragma once
#include "vrptw/Instance.hpp"
#include <vector>
#include <cmath>
#include <cstddef>
#include <stdexcept>

namespace vrptw {

// Precomputed distance matrix. This is the SINGLE place where distances are
// computed, so every algorithm sees identical values (a core fairness
// requirement). By default the travel TIME between i and j equals this distance
// (the classic Solomon/DIMACS convention), so `time(i,j) == (*this)(i,j)`.
//
// Convention (benchmark): distances are TRUNCATED to one decimal place, d_ij =
// trunc(euclidean * 10) / 10. This was validated empirically: only truncation
// reproduces the 56 Dinamics/SINTEF reference costs exactly (e.g. C101 = 827.3).
//
// REAL ROAD NETWORKS (Digital Twin): load_distance()/load_time() override the
// matrices with EXPLICIT values (e.g. OSRM road distances in metres and driving
// durations in seconds). When a separate time matrix is loaded, time != distance:
// the objective uses operator() (distance) while the time windows use time().
// With no time matrix loaded, time() falls back to the distance — so the
// benchmark behaviour is byte-identical.
class DistanceMatrix {
public:
    static double truncate1(double v) { return std::trunc(v * 10.0) / 10.0; }

    explicit DistanceMatrix(const Instance& inst) : n_(static_cast<int>(inst.size())) {
        d_.assign(static_cast<std::size_t>(n_) * n_, 0.0);
        for (int i = 0; i < n_; ++i) {
            for (int j = 0; j < n_; ++j) {
                const double dx = inst.node(i).x - inst.node(j).x;
                const double dy = inst.node(i).y - inst.node(j).y;
                d_[idx(i, j)] = truncate1(std::sqrt(dx * dx + dy * dy));
            }
        }
    }

    double operator()(int i, int j) const { return d_[idx(i, j)]; }      // distance (cost)
    double time(int i, int j) const { return t_.empty() ? d_[idx(i, j)] : t_[idx(i, j)]; }
    bool   has_time() const { return !t_.empty(); }
    int    n() const { return n_; }

    // Override with an explicit n*n matrix (row-major). For real road networks.
    void load_distance(const std::vector<double>& m) { check(m); d_ = m; }
    void load_time(const std::vector<double>& m) { check(m); t_ = m; }

private:
    std::size_t idx(int i, int j) const {
        return static_cast<std::size_t>(i) * n_ + j;
    }
    void check(const std::vector<double>& m) const {
        if (m.size() != static_cast<std::size_t>(n_) * n_)
            throw std::runtime_error("matriz com dimensao incompativel com a instancia");
    }
    int                 n_;
    std::vector<double> d_;
    std::vector<double> t_;   // empty => time == distance
};

// Euclidean matrix built EXPLICITLY, so the numeric convention is chosen at the
// call site instead of being baked into the constructor above. Injected through
// load_distance(), the same extension point the Digital Twin already uses, which
// is why `--dist-mode trunc` (the default) never calls this and the 56/56
// reference gate is immune by construction.
//
//   truncate = true   d_ij = trunc(euclid * 10)/10   -- 12th DIMACS convention
//   truncate = false  d_ij = euclid                  -- full double precision
//
// Solomon (1987) used the latter: he reports his best C1 solution as "a distance
// of 829 units", and those very routes cost 828.94 in double precision but 827.3
// truncated. Use double precision ONLY when comparing against his Tables I-VI;
// gaps against the CVRPLIB best-known are meaningless under it.
inline std::vector<double> make_euclid_matrix(const Instance& inst, bool truncate) {
    const int n = static_cast<int>(inst.size());
    std::vector<double> m(static_cast<std::size_t>(n) * static_cast<std::size_t>(n), 0.0);
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            const double dx = inst.node(i).x - inst.node(j).x;
            const double dy = inst.node(i).y - inst.node(j).y;
            const double d  = std::sqrt(dx * dx + dy * dy);
            m[static_cast<std::size_t>(i) * static_cast<std::size_t>(n) + static_cast<std::size_t>(j)] =
                truncate ? DistanceMatrix::truncate1(d) : d;
        }
    }
    return m;
}

} // namespace vrptw
