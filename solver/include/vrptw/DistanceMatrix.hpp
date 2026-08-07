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

} // namespace vrptw
