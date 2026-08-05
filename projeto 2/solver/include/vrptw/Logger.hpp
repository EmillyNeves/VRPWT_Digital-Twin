#pragma once
#include "vrptw/Solution.hpp"
#include <vector>
#include <string>
#include <fstream>

namespace vrptw {

struct ConvPoint { long ms; double best; };

// Records the convergence trace (best-so-far vs elapsed time) and, optionally,
// per-move solution snapshots for the route-evolution plots. Snapshot line:
//   idx;ms;cost;movetype;r1c1,r1c2,...|r2c1,r2c2,...|...
class Logger {
public:
    void on_improve(long ms, double best) { conv_.push_back({ms, best}); }
    const std::vector<ConvPoint>& convergence() const { return conv_; }

    void write_convergence(const std::string& path) const {
        std::ofstream f(path);
        f << "elapsed_ms,best\n";
        for (const auto& p : conv_) f << p.ms << ',' << p.best << '\n';
    }

    void enable_snapshots(const std::string& path, int stride) {
        snap_.open(path);
        snap_stride_ = stride < 1 ? 1 : stride;
    }
    bool snapshots_enabled() const { return snap_.is_open(); }

    // Call after every accepted move (idx = sequential move index).
    void on_move(int idx, long ms, double cost, const Solution& s, const char* movetype) {
        if (!snap_.is_open() || (idx % snap_stride_) != 0) return;
        snap_ << idx << ';' << ms << ';' << cost << ';' << movetype << ';';
        bool first_route = true;
        for (const auto& r : s.routes) {
            if (r.empty()) continue;
            if (!first_route) snap_ << '|';
            first_route = false;
            bool first_c = true;
            for (int c : r.seq) { if (!first_c) snap_ << ','; first_c = false; snap_ << c; }
        }
        snap_ << '\n';
    }

private:
    std::vector<ConvPoint> conv_;
    std::ofstream          snap_;
    int                    snap_stride_ = 1;
};

} // namespace vrptw
