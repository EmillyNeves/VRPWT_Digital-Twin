#pragma once
#include <string>
#include <vector>
#include <cstddef>

namespace vrptw {

// A node of the VRPTW. Node 0 is the depot. Times follow the Solomon
// convention: travel time between i and j equals the Euclidean distance,
// service starts at max(arrival, ready) and must begin no later than `due`.
struct Customer {
    int    id      = 0;
    double x       = 0.0;
    double y       = 0.0;
    double demand  = 0.0;
    double ready   = 0.0;   // earliest service start
    double due     = 0.0;   // latest service start
    double service = 0.0;   // service duration
};

// Immutable problem data parsed from a Solomon instance file.
class Instance {
public:
    std::string           name;
    double                capacity = 0.0;  // homogeneous fleet capacity (200 type 1, 1000 type 2)
    int                   vehicles = 0;    // informational fleet upper bound
    std::vector<Customer> nodes;           // index 0 = depot

    std::size_t     size()          const { return nodes.size(); }            // depot + customers
    int             num_customers() const { return static_cast<int>(nodes.size()) - 1; }
    const Customer& depot()         const { return nodes[0]; }
    const Customer& node(int i)     const { return nodes[static_cast<std::size_t>(i)]; }
};

} // namespace vrptw
