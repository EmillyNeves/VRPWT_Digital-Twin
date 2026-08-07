#pragma once
#include "vrptw/Instance.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include <vector>
#include <algorithm>
#include <limits>

namespace vrptw {

inline constexpr double kEps = 1e-6;

// A single vehicle route. `seq` holds customer ids in visiting order; the
// depot is implicit at both ends. The cached arrays enable O(1)/O(segment)
// delta-evaluation of moves (filled by recompute()).
struct Route {
    std::vector<int>    seq;

    // caches (valid after recompute)
    double              load        = 0.0;
    double              distance    = 0.0;
    bool                feasible    = true;
    bool                cap_ok      = true;
    bool                tw_ok       = true;
    std::vector<double> arrival;     // arrival time at seq[k]
    std::vector<double> start;       // service start = max(arrival, ready)
    std::vector<double> departure;   // start + service
    std::vector<double> tw_slack;    // max forward shift of start[k] keeping feasibility (push-forward)

    bool empty() const { return seq.empty(); }
    std::size_t len() const { return seq.size(); }

    void recompute(const Instance& inst, const DistanceMatrix& dm) {
        const std::size_t m = seq.size();
        arrival.assign(m, 0.0);
        start.assign(m, 0.0);
        departure.assign(m, 0.0);
        tw_slack.assign(m, 0.0);
        load = 0.0;
        distance = 0.0;
        tw_ok = true;

        double t = inst.depot().ready;   // depart depot at time 0
        int prev = 0;
        for (std::size_t k = 0; k < m; ++k) {
            const int c = seq[k];
            distance += dm(prev, c);            // cost uses the distance matrix
            arrival[k] = t + dm.time(prev, c);  // schedule uses the time matrix (== distance by default)
            const Customer& cust = inst.node(c);
            start[k] = std::max(arrival[k], cust.ready);
            if (start[k] > cust.due + kEps) tw_ok = false;
            departure[k] = start[k] + cust.service;
            load += cust.demand;
            t = departure[k];
            prev = c;
        }
        // return to depot
        double arrival_depot = t;
        if (m > 0) {
            distance += dm(prev, 0);
            arrival_depot = t + dm.time(prev, 0);
        }
        if (arrival_depot > inst.depot().due + kEps) tw_ok = false;

        cap_ok = (load <= inst.capacity + kEps);
        feasible = tw_ok && cap_ok;

        // backward push-forward slack pass
        const double slack_return = inst.depot().due - arrival_depot;
        double slack_after = slack_return;
        double wait_after = 0.0;   // no waiting at depot return
        for (std::size_t kk = m; kk-- > 0;) {
            const Customer& cust = inst.node(seq[kk]);
            const double own = cust.due - start[kk];
            tw_slack[kk] = std::min(own, wait_after + slack_after);
            // prepare for kk-1: the "after" node becomes kk
            wait_after = start[kk] - arrival[kk];   // waiting time at kk
            slack_after = tw_slack[kk];
            if (kk == 0) break;
        }
    }
};

} // namespace vrptw
