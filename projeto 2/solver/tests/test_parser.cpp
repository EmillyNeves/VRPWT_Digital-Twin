#include "test_framework.hpp"
#include "vrptw/InstanceParser.hpp"
#include <filesystem>
#include <string>

using namespace vrptw;
namespace fs = std::filesystem;

TEST(parser_c101_fields) {
    const Instance inst = parse_instance((fs::path(PROJECT_ROOT) / "input" / "C101.txt").string());
    CHECK(inst.num_customers() == 100);
    CHECK(inst.size() == 101);
    CHECK_NEAR(inst.capacity, 200.0, 1e-9);
    CHECK(inst.depot().id == 0);
    CHECK_NEAR(inst.depot().ready, 0.0, 1e-9);
    CHECK_NEAR(inst.depot().due, 1236.0, 1e-9);
    // customer 1 row: "1 45 68 10 912 967 90"
    const Customer& c1 = inst.node(1);
    CHECK_NEAR(c1.x, 45.0, 1e-9);
    CHECK_NEAR(c1.y, 68.0, 1e-9);
    CHECK_NEAR(c1.demand, 10.0, 1e-9);
    CHECK_NEAR(c1.ready, 912.0, 1e-9);
    CHECK_NEAR(c1.due, 967.0, 1e-9);
    CHECK_NEAR(c1.service, 90.0, 1e-9);
}

TEST(parser_r201_is_type2_capacity) {
    const Instance inst = parse_instance((fs::path(PROJECT_ROOT) / "input" / "R201.txt").string());
    CHECK(inst.num_customers() == 100);
    CHECK_NEAR(inst.capacity, 1000.0, 1e-9);
}
