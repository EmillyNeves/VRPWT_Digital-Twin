#pragma once
#include <chrono>

namespace vrptw {

// Wall-clock stopping criterion shared identically by all metaheuristics, so
// every algorithm gets the same CPU-time budget per instance (fairness).
// A negative budget means "no time limit" (used by the deterministic methods).
class StoppingCriterion {
public:
    explicit StoppingCriterion(long budget_ms) : budget_ms_(budget_ms), t0_(Clock::now()) {}

    long elapsed_ms() const {
        return static_cast<long>(
            std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - t0_).count());
    }
    bool should_stop() const { return budget_ms_ >= 0 && elapsed_ms() >= budget_ms_; }
    void reset() { t0_ = Clock::now(); }

private:
    using Clock = std::chrono::steady_clock;
    long             budget_ms_;
    Clock::time_point t0_;
};

} // namespace vrptw
