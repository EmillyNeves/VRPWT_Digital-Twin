#include "test_framework.hpp"
#include "vrptw/InstanceParser.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include <filesystem>
#include <cmath>

using namespace vrptw;
namespace fs = std::filesystem;

TEST(distance_truncated_symmetry_diagonal) {
    const Instance inst = parse_instance((fs::path(PROJECT_ROOT) / "data" / "instances" / "solomon" / "C101.txt").string());
    const DistanceMatrix dm(inst);
    // depot (40,50) -> customer 1 (45,68): sqrt(5^2 + 18^2) = sqrt(349) ~ 18.6815,
    // truncated to 1 decimal place = 18.6 (Solomon/DIMACS convention).
    CHECK_NEAR(dm(0, 1), 18.6, 1e-9);
    CHECK_NEAR(dm(1, 0), dm(0, 1), 1e-12);   // symmetry
    CHECK_NEAR(dm(7, 7), 0.0, 1e-12);        // zero diagonal
    CHECK(dm(0, 1) <= std::sqrt(349.0));     // truncation never increases distance
}
