#pragma once
#include <iostream>
#include <string>
#include <vector>
#include <functional>
#include <cmath>

// Minimal self-contained test harness (no external dependency). Tests register
// themselves with the TEST(name) macro; main() calls tf::run_all().
namespace tf {

struct TestCase { std::string name; std::function<void()> fn; };

inline std::vector<TestCase>& registry() { static std::vector<TestCase> r; return r; }
inline int& failures() { static int f = 0; return f; }

struct Registrar {
    Registrar(std::string n, std::function<void()> f) {
        registry().push_back({std::move(n), std::move(f)});
    }
};

inline int run_all() {
    int passed = 0, failed = 0;
    for (auto& tc : registry()) {
        const int before = failures();
        try {
            tc.fn();
        } catch (const std::exception& e) {
            std::cerr << "  [EXCECAO] " << e.what() << "\n";
            ++failures();
        }
        if (failures() == before) { std::cout << "[PASS] " << tc.name << "\n"; ++passed; }
        else                      { std::cout << "[FAIL] " << tc.name << "\n"; ++failed; }
    }
    std::cout << "\n" << passed << " passou, " << failed << " falhou\n";
    return failed == 0 ? 0 : 1;
}

} // namespace tf

#define TEST(name)                                                   \
    static void name();                                              \
    static tf::Registrar tf_reg_##name(#name, name);                 \
    static void name()

#define CHECK(cond)                                                  \
    do {                                                             \
        if (!(cond)) {                                               \
            std::cerr << "  CHECK falhou: " << #cond                 \
                      << "  @ " << __FILE__ << ":" << __LINE__ << "\n"; \
            ++tf::failures();                                        \
        }                                                            \
    } while (0)

#define CHECK_NEAR(a, b, tol)                                        \
    do {                                                             \
        const double _a = (a), _b = (b), _t = (tol);                 \
        if (std::fabs(_a - _b) > _t) {                               \
            std::cerr << "  CHECK_NEAR falhou: " << #a << "=" << _a   \
                      << " vs " << #b << "=" << _b << " (tol " << _t  \
                      << ")  @ " << __FILE__ << ":" << __LINE__ << "\n"; \
            ++tf::failures();                                        \
        }                                                            \
    } while (0)
