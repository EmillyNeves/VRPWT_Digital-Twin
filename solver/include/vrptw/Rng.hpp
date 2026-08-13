#pragma once
#include <cstdint>
#include <random>
#include <string>

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

// PROTOCOLO DE SEMENTE: o PRNG de uma execucao e semeado com
//
//     FNV-1a(nome da instancia) XOR (semente da execucao * constante impar)
//
// A semente da execucao (1..R, registrada no CSV) identifica a execucao; o hash
// da instancia descorrelaciona os fluxos entre instancias com a mesma semente.
//
// FNV-1a e usado NO LUGAR de std::hash porque std::hash<std::string> e
// implementation-defined: o mesmo programa em outra libstdc++ produziria outros
// fluxos aleatorios, e a reprodutibilidade prometida no relatorio valeria so na
// maquina original. FNV-1a e especificado byte a byte -- mesmo resultado em
// qualquer plataforma. (E o mesmo hash usado no baseline congelado dos testes.)
inline std::uint64_t fnv1a(const std::string& s) {
    std::uint64_t h = 1469598103934665603ull;             // offset basis
    for (unsigned char c : s) { h ^= c; h *= 1099511628211ull; }  // FNV prime
    return h;
}

inline std::uint64_t make_seed(std::uint64_t base, const std::string& instance) {
    return fnv1a(instance) ^ (base * 0x9E3779B97F4A7C15ull);
}

} // namespace vrptw
