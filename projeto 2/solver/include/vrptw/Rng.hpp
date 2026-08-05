#pragma once
#include <cstdint>
#include <random>
#include <string>
#include <functional>

namespace vrptw {

// The single source of randomness. Seeded deterministically so any run is
// reproducible from its logged seed.
class Rng {
public:
    explicit Rng(std::uint64_t seed) : eng_(seed) {}

    int    uniform_int(int lo, int hi) { return std::uniform_int_distribution<int>(lo, hi)(eng_); }
    double uniform_real(double lo = 0.0, double hi = 1.0) {
        return std::uniform_real_distribution<double>(lo, hi)(eng_);
    }
    std::mt19937_64& engine() { return eng_; }

private:
    std::mt19937_64 eng_;
};

// Seed protocol: mix a base seed, the instance name, and the run index so each
// (instance, run) is independent yet reproducible.
inline std::uint64_t make_seed(std::uint64_t base, const std::string& instance, int run) {
    const std::uint64_t h = std::hash<std::string>{}(instance);
    return base ^ (h * 0x9E3779B97F4A7C15ull) ^ (static_cast<std::uint64_t>(run) * 0xD1B54A32D192ED03ull);
}

} // namespace vrptw
