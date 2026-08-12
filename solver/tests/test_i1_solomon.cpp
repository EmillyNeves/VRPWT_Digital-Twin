// Fidelity checks for Solomon's I1 insertion heuristic (Solomon 1987).
//
// These guard the refactoring that extracts the shared I1 core (used by both
// solomon_i1() and the GRASP randomized construction) and that exposes the c12
// time term. See docs/verificacao/01-solomon-i1.md.
#include "test_framework.hpp"
#include "vrptw/InstanceParser.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Validator.hpp"
#include "vrptw/Evaluator.hpp"
#include "vrptw/Neighborhoods.hpp"
#include "vrptw/SolutionIO.hpp"
#include "vrptw/algorithms/SolomonI1.hpp"
#include <filesystem>
#include <algorithm>
#include <cstdint>
#include <string>
#include <vector>
#include <iostream>

using namespace vrptw;
namespace fs = std::filesystem;

namespace {

// FNV-1a 64. Deterministic and trivially reimplementable in any language, so the
// frozen values below can be regenerated outside C++ if ever needed.
std::uint64_t fnv1a64(const std::string& s) {
    std::uint64_t h = 14695981039346656037ULL;
    for (unsigned char b : s) { h ^= b; h *= 1099511628211ULL; }
    return h;
}

// Canonical serialization of a solution: routes in order, customers separated by
// a space, routes separated by '|'. Empty routes are skipped, matching
// write_solution() in SolutionIO.cpp.
std::string canonical(const Solution& s) {
    std::string out;
    for (const auto& r : s.routes) {
        if (r.empty()) continue;
        if (!out.empty()) out += '|';
        for (std::size_t i = 0; i < r.seq.size(); ++i) {
            if (i) out += ' ';
            out += std::to_string(r.seq[i]);
        }
    }
    return out;
}

struct Frozen { const char* name; int vehicles; double dist; std::uint64_t hash; };

// Baseline frozen from the implementation BEFORE the shared-core refactoring,
// with I1Params{} defaults (mu=1, lambda=2, alpha1=1, alpha2=0, seed=farthest).
// Route sequences are hashed, not just (K, distance): two different solutions
// can share both aggregates.
//
// If this test fails, the refactoring changed the default behaviour. DO NOT
// update these literals to make it pass -- find out what changed and why.
const Frozen kBaseline[] = {
    {"C101", 10, 922.0, 0x236f5ef3db55e192ULL},
    {"C102", 10, 1039.7, 0x3dab678fc57abf3aULL},
    {"C103", 11, 1221.7, 0xd7556b2b28557794ULL},
    {"C104", 10, 1148.2, 0x03c5148cb159be7cULL},
    {"C105", 10, 878.9, 0xe1e33f9b831dea24ULL},
    {"C106", 11, 951.2, 0x333b02a61e91204cULL},
    {"C107", 10, 902.4, 0xb2d631c90e67cb54ULL},
    {"C108", 10, 975.2, 0x96f5d1d51747de74ULL},
    {"C109", 11, 933.1, 0x1b24dbf36ba53994ULL},
    {"C201", 3, 609.1, 0xbe5b0ea7423df1e2ULL},
    {"C202", 4, 793.0, 0x1cebfadf6af2c1b2ULL},
    {"C203", 4, 931.4, 0x3fdb2e1365824c00ULL},
    {"C204", 4, 1138.4, 0x76413cf77a0daf84ULL},
    {"C205", 4, 667.6, 0xcc7779da7935cae8ULL},
    {"C206", 3, 660.6, 0x3a6c9a9690c19ab6ULL},
    {"C207", 3, 747.1, 0x7d6f273e72c2b992ULL},
    {"C208", 3, 717.6, 0x467c4a45f6483c0cULL},
    {"R101", 21, 1867.1, 0xc5745bc6cdde571cULL},
    {"R102", 19, 1711.0, 0x5461ac90a8b85e42ULL},
    {"R103", 16, 1550.0, 0x894b43c549e8b404ULL},
    {"R104", 12, 1267.5, 0xaa53b5415455809eULL},
    {"R105", 15, 1593.4, 0xe69478db7787c7f0ULL},
    {"R106", 14, 1446.6, 0x3c24d71dbcefd486ULL},
    {"R107", 12, 1354.1, 0x3f70139c2b3fe0caULL},
    {"R108", 11, 1226.0, 0xf39a7ac07a0b1de2ULL},
    {"R109", 14, 1457.8, 0xac615c90dd05e65eULL},
    {"R110", 12, 1339.0, 0x6dd12098fa96ad8eULL},
    {"R111", 12, 1276.6, 0x011a39eb39293088ULL},
    {"R112", 11, 1188.1, 0x72e4ca1ecc31981eULL},
    {"R201", 5, 1805.3, 0x79b9735163f66b3cULL},
    {"R202", 4, 1585.0, 0x017c268e5dc75100ULL},
    {"R203", 4, 1534.3, 0x20cfa243264b4e80ULL},
    {"R204", 4, 1155.2, 0x464806ca9e765ee0ULL},
    {"R205", 4, 1403.3, 0xe82453d6d8989686ULL},
    {"R206", 3, 1303.5, 0x6323c75fef4ccfd8ULL},
    {"R207", 3, 1169.9, 0xd9e577b41dec71b8ULL},
    {"R208", 3, 974.0, 0x700d82c88069acf2ULL},
    {"R209", 4, 1322.5, 0xc8ed2ab61bba817eULL},
    {"R210", 4, 1404.0, 0xe206d5be1af63354ULL},
    {"R211", 3, 1013.4, 0x008c8256dad77622ULL},
    {"RC101", 17, 1920.4, 0xcb56564ac0f50356ULL},
    {"RC102", 15, 1813.3, 0xc2769697b3b758d8ULL},
    {"RC103", 12, 1544.5, 0xbf2adc4173508edaULL},
    {"RC104", 12, 1380.6, 0x08750ed0c9f27306ULL},
    {"RC105", 16, 1838.0, 0x63ac4220cbfd63acULL},
    {"RC106", 14, 1726.5, 0x85f30a571eb5fd6aULL},
    {"RC107", 13, 1587.4, 0xf54524e6d91446faULL},
    {"RC108", 11, 1368.2, 0x5858c70a763c915eULL},
    {"RC201", 5, 2025.4, 0x09a2ac03c73b5316ULL},
    {"RC202", 4, 1783.8, 0xcd1730e6a00f6a40ULL},
    {"RC203", 4, 1528.8, 0x1a49f29b59f0d556ULL},
    {"RC204", 4, 1254.4, 0xaf134feb541ded78ULL},
    {"RC205", 5, 2179.4, 0x9b8e34c2d6a73352ULL},
    {"RC206", 4, 1743.1, 0x4e8a28e29d6d9624ULL},
    {"RC207", 4, 1565.7, 0x1dfdc6830815a502ULL},
    {"RC208", 3, 1155.9, 0xa4d9317021263eb6ULL},
};

fs::path instance_path(const std::string& name) {
    return fs::path(PROJECT_ROOT) / "data" / "instances" / "solomon" / (name + ".txt");
}

// Independent forward simulation of a sequence: service start at each position
// plus the arrival back at the depot. Deliberately does NOT use Route's caches,
// so it can serve as the oracle for the O(1) eval_insert.
struct Walk { std::vector<double> start; double depot_arrival = 0.0; };

Walk walk(const Instance& inst, const DistanceMatrix& dm, const std::vector<int>& seq) {
    Walk w;
    double t = inst.depot().ready;
    int prev = 0;
    for (int c : seq) {
        t += dm.time(prev, c);
        const Customer& cu = inst.node(c);
        if (t < cu.ready) t = cu.ready;
        w.start.push_back(t);
        t += cu.service;
        prev = c;
    }
    w.depot_arrival = t + dm.time(prev, 0);
    return w;
}

} // namespace

// REGRESSION GUARD. The default I1 must keep producing byte-for-byte the same
// routes after the shared-core extraction.
TEST(i1_default_bit_identical) {
    int matched = 0;
    const int total = static_cast<int>(std::size(kBaseline));
    for (const auto& f : kBaseline) {
        const Instance inst = parse_instance(instance_path(f.name).string());
        const DistanceMatrix dm(inst);
        const Evaluator ev(inst, dm);
        const Solution sol = solomon_i1(inst, dm);

        const int    veh  = sol.num_vehicles();
        const double dist = Evaluator::round1(ev.primary(sol));
        const std::uint64_t h = fnv1a64(canonical(sol));

        CHECK(veh == f.vehicles);
        CHECK_NEAR(dist, f.dist, 1e-9);
        CHECK(h == f.hash);
        if (veh == f.vehicles && h == f.hash) ++matched;
        else std::cout << "  -> " << f.name << ": K=" << veh << " (esperado " << f.vehicles
                       << "), dist=" << dist << " (esperado " << f.dist << ")\n";
    }
    std::cout << "  [I1 baseline] identicas=" << matched << "/" << total << "\n";
    CHECK(matched == total);
}

// Solomon's four reported quantities are not independent: with travel time equal
// to distance, every feasible schedule satisfies
//     schedule_time == distance + waiting_time + service_time
// and service_time is a per-instance constant (9000 for the C families, 1000 for
// R and RC). This identity is what lets us compare against Tables I-VI on the
// VARIABLE part (distance + waiting) instead of on the service-inflated total.
TEST(i1_schedule_identity) {
    int checked = 0;
    for (const auto& f : kBaseline) {
        const Instance inst = parse_instance(instance_path(f.name).string());
        const DistanceMatrix dm(inst);
        const Solution sol = solomon_i1(inst, dm);
        const ValidationResult vr = validate(inst, dm, sol);

        CHECK(vr.feasible);
        CHECK_NEAR(vr.schedule_time, vr.distance + vr.waiting_time + vr.service_time, 1e-6);
        ++checked;
    }
    std::cout << "  [identidade] schedule == distancia + espera + servico em "
              << checked << " instancias\n";
    CHECK(checked == 56);
}

// The service total must be the per-family constant Solomon's tables imply
// (derivable from his own numbers: R1 1436.7 + 258.8 + 1000 = 2695.5).
TEST(i1_service_time_is_family_constant) {
    for (const auto& f : kBaseline) {
        const Instance inst = parse_instance(instance_path(f.name).string());
        const DistanceMatrix dm(inst);
        const ValidationResult vr = validate(inst, dm, solomon_i1(inst, dm));
        // C1/C2 have service 90 per customer, R and RC have 10 ("RC" starts with 'R')
        const double expected = (f.name[0] == 'C') ? 9000.0 : 1000.0;
        CHECK_NEAR(vr.service_time, expected, 1e-6);
    }
}

// THE HIGHEST-LEVERAGE CHECK. eval_insert computes c12 (the push forward at the
// successor) in O(1) from Route's caches. Here we recompute it in O(n) by walking
// the modified sequence from scratch and requiring the two to agree. A bug here
// silently corrupts I1, GRASP and anything else built on the criterion.
TEST(insert_eval_dtime_matches_bruteforce) {
    const char* kInstances[] = {"C101", "C201", "R101", "R201", "RC101", "RC201"};
    long checked = 0, at_end = 0, nonzero = 0;

    for (const char* name : kInstances) {
        const Instance inst = parse_instance(instance_path(name).string());
        const DistanceMatrix dm(inst);
        Solution sol = solomon_i1(inst, dm);
        sol.recompute_all(inst, dm);

        // An I1 route is packed tight, so inserting a foreign customer is almost
        // never feasible. Instead REMOVE one customer and reinsert it: position k
        // is then feasible by construction, which guarantees the check has teeth.
        for (const Route& full : sol.routes) {
            for (std::size_t k = 0; k < full.len(); ++k) {
                Route rr = full;
                const int u = rr.seq[k];
                rr.seq.erase(rr.seq.begin() + static_cast<std::ptrdiff_t>(k));
                rr.recompute(inst, dm);

                const Walk before = walk(inst, dm, rr.seq);
                const int m = static_cast<int>(rr.len());

                for (int pos = 0; pos <= m; ++pos) {
                    const InsertEval ie = eval_insert(inst, dm, rr, pos, u);
                    if (!ie.feasible) continue;

                    std::vector<int> mod = rr.seq;
                    mod.insert(mod.begin() + pos, u);
                    const Walk after = walk(inst, dm, mod);

                    // c12 = b_ju - b_j: delay induced at the successor. At the end
                    // of the route the successor is the depot (see InsertEval).
                    const double expected = (pos == m)
                        ? after.depot_arrival - before.depot_arrival
                        : after.start[static_cast<std::size_t>(pos) + 1] -
                          before.start[static_cast<std::size_t>(pos)];
                    CHECK_NEAR(ie.dtime, expected, 1e-9);

                    const int pred = (pos == 0) ? 0 : rr.seq[static_cast<std::size_t>(pos) - 1];
                    const int succ = (pos == m) ? 0 : rr.seq[static_cast<std::size_t>(pos)];
                    CHECK_NEAR(ie.ddist, dm(pred, u) + dm(u, succ) - dm(pred, succ), 1e-9);

                    ++checked;
                    if (pos == m) ++at_end;
                    if (ie.dtime > 1e-9) ++nonzero;
                }
            }
        }
    }
    std::cout << "  [c12] insercoes verificadas=" << checked
              << " (no fim da rota=" << at_end << ", com atraso>0=" << nonzero << ")\n";
    CHECK(checked > 100);      // the check must actually have exercised something
    CHECK(at_end > 0);         // including the depot-successor branch
    CHECK(nonzero > 0);        // and cases where the push forward is not trivially zero
}

// Solomon's second seeding criterion (p.259): "the unrouted customer with the
// earliest deadline". Ties broken by lowest id (S3 -- the article is silent).
TEST(i1_seed_earliest_deadline) {
    for (const char* name : {"C101", "R101", "RC201"}) {
        const Instance inst = parse_instance(instance_path(name).string());
        const DistanceMatrix dm(inst);
        const int n = static_cast<int>(inst.size());
        std::vector<char> routed(static_cast<std::size_t>(n), 0);
        routed[0] = 1;

        const int got = i1_select_seed(inst, dm, routed, I1Seed::EarliestDeadline);
        int expect = -1;
        for (int u = 1; u < n; ++u)
            if (expect < 0 || inst.node(u).due < inst.node(expect).due) expect = u;
        CHECK(got == expect);

        // and the two rules must genuinely differ, otherwise the option is vacuous
        const int far = i1_select_seed(inst, dm, routed, I1Seed::FarthestFromDepot);
        CHECK(far >= 1 && far < n);
        std::cout << "  [semente] " << name << ": prazo=" << got
                  << " (due=" << inst.node(got).due << ")  distante=" << far
                  << " (d=" << dm(0, far) << ")\n";
    }
}

// With alpha2 = 0 the time term must not influence anything: the frozen baseline
// already proves the default, so here we assert the converse -- that turning
// alpha2 on DOES change the outcome, i.e. the new parameter is really wired in.
TEST(i1_alpha2_actually_changes_the_solution) {
    I1Params time_ins;                 // Solomon's (1,2,0,1): pure time insertion
    time_ins.alpha1 = 0.0;
    time_ins.alpha2 = 1.0;

    int differed = 0;
    for (const char* name : {"C201", "R201", "RC201"}) {
        const Instance inst = parse_instance(instance_path(name).string());
        const DistanceMatrix dm(inst);
        const Solution a = solomon_i1(inst, dm);              // defaults: distance insertion
        const Solution b = solomon_i1(inst, dm, time_ins);    // time insertion
        const ValidationResult vb = validate(inst, dm, b);
        CHECK(vb.feasible);                                   // must stay feasible
        if (canonical(a) != canonical(b)) ++differed;
    }
    std::cout << "  [alpha2] solucoes diferentes de alpha2=0 em " << differed << "/3 instancias\n";
    CHECK(differed == 3);
}

// EXACT ANCHOR for the double-precision path. Seven SINTEF files carry the
// full-precision Euclidean cost of their own routes in the "Reference" field.
// Recomputing those routes under --dist-mode double must reproduce the value to
// machine precision; under truncation it must NOT (otherwise the anchor would be
// unable to tell the two conventions apart, and would prove nothing).
TEST(double_precision_refs) {
    struct A { const char* inst; const char* sintef; };
    const A kAnchors[] = {
        {"R112", "r112"}, {"R203", "r203"}, {"R207", "r207"}, {"R211", "r211"},
        {"RC107", "rc107"}, {"RC202", "rc202"}, {"RC203", "rc203"},
    };
    const fs::path sdir = fs::path(PROJECT_ROOT) / "data" / "reference-solutions" / "sintef";

    int anchored = 0, discriminated = 0;
    for (const auto& a : kAnchors) {
        const auto ps = read_solution_file((sdir / (std::string(a.sintef) + ".txt")).string());
        CHECK(ps.reference.has_value());
        if (!ps.reference) continue;

        const Instance inst = parse_instance(instance_path(a.inst).string());

        DistanceMatrix dbl(inst);
        dbl.load_distance(make_euclid_matrix(inst, false));
        const ValidationResult vd = validate(inst, dbl, to_solution(ps, inst, dbl));
        CHECK(vd.feasible);
        CHECK_NEAR(vd.distance, *ps.reference, 1e-6);
        if (std::fabs(vd.distance - *ps.reference) <= 1e-6) ++anchored;

        const DistanceMatrix tr(inst);                       // default: truncated
        const ValidationResult vt = validate(inst, tr, to_solution(ps, inst, tr));
        if (std::fabs(vt.distance - *ps.reference) > 0.5) ++discriminated;
    }
    std::cout << "  [precisao dupla] ancoras batendo=" << anchored << "/7"
              << ", truncamento distinguivel em " << discriminated << "/7\n";
    CHECK(anchored == 7);
    CHECK(discriminated == 7);
}

// The other 49 SINTEF files hold prose in "Reference" ("... Springer 2007.",
// "N/A", a URL). Reading "2007." as a cost would silently corrupt the anchor.
TEST(reference_field_rejects_prose) {
    const fs::path sdir = fs::path(PROJECT_ROOT) / "data" / "reference-solutions" / "sintef";
    int with_number = 0, total = 0;
    for (const auto& e : fs::directory_iterator(sdir)) {
        if (e.path().extension() != ".txt") continue;
        ++total;
        if (read_solution_file(e.path().string()).reference) ++with_number;
    }
    std::cout << "  [Reference] numericas=" << with_number << "/" << total << "\n";
    CHECK(total == 56);
    CHECK(with_number == 7);      // exactly the seven anchors, no prose misparsed
}
