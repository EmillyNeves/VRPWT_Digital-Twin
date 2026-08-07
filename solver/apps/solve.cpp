#include "vrptw/InstanceParser.hpp"
#include "vrptw/DistanceMatrix.hpp"
#include "vrptw/Solution.hpp"
#include "vrptw/SolutionIO.hpp"
#include "vrptw/Evaluator.hpp"
#include "vrptw/Validator.hpp"
#include "vrptw/Timer.hpp"
#include "vrptw/Logger.hpp"
#include "vrptw/Rng.hpp"
#include "vrptw/algorithms/SolomonI1.hpp"
#include "vrptw/algorithms/VND.hpp"
#include "vrptw/algorithms/Grasp.hpp"
#include "vrptw/algorithms/TabuSearch.hpp"

#include <iostream>
#include <iomanip>
#include <fstream>
#include <map>
#include <string>
#include <sstream>
#include <vector>
#include <chrono>
#include <filesystem>

using namespace vrptw;

namespace {

struct Args {
    std::map<std::string, std::string> kv;
    bool has(const std::string& k) const { return kv.count(k) > 0; }
    std::string get(const std::string& k, const std::string& def = "") const {
        auto it = kv.find(k);
        return it == kv.end() ? def : it->second;
    }
    long getl(const std::string& k, long def) const {
        auto it = kv.find(k);
        return it == kv.end() ? def : std::stol(it->second);
    }
};

Args parse_args(int argc, char** argv) {
    Args a;
    for (int i = 1; i < argc; ++i) {
        std::string s = argv[i];
        if (s.rfind("--", 0) == 0) {
            const std::string key = s.substr(2);
            if (i + 1 < argc && std::string(argv[i + 1]).rfind("--", 0) != 0) {
                a.kv[key] = argv[++i];
            } else {
                a.kv[key] = "1";   // flag
            }
        }
    }
    return a;
}

// Read an n*n matrix (row-major) of doubles from a text file. An optional
// leading token equal to n (the matrix order) is tolerated. Used to inject
// real road-network distance/time matrices (Digital Twin).
std::vector<double> read_matrix(const std::string& path, int n) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("nao foi possivel abrir a matriz: " + path);
    std::vector<double> v;
    double x;
    while (in >> x) v.push_back(x);
    if (static_cast<int>(v.size()) == n * n + 1) v.erase(v.begin());   // tolerate a leading n
    if (static_cast<int>(v.size()) != n * n)
        throw std::runtime_error("matriz com " + std::to_string(v.size()) +
                                 " valores; esperado " + std::to_string(n * n));
    return v;
}

// Parse a comma-separated neighbourhood subset (for the ablation study), e.g.
// "relocate,oropt,swap,twoopt,cross". Unknown tokens are ignored.
std::vector<Neighborhood> parse_neighborhoods(const std::string& s) {
    std::vector<Neighborhood> order;
    std::stringstream ss(s);
    std::string tok;
    while (std::getline(ss, tok, ',')) {
        if      (tok == "relocate")                      order.push_back(Neighborhood::Relocate);
        else if (tok == "swap")                          order.push_back(Neighborhood::Swap);
        else if (tok == "twoopt" || tok == "2opt")       order.push_back(Neighborhood::TwoOpt);
        else if (tok == "oropt")                         order.push_back(Neighborhood::OrOpt);
        else if (tok == "cross" || tok == "crossexchange") order.push_back(Neighborhood::CrossExchange);
    }
    return order;
}

} // namespace

int main(int argc, char** argv) {
    const Args args = parse_args(argc, argv);
    const std::string algo = args.get("algo", "i1");
    const std::string inst_path = args.get("instance");
    if (inst_path.empty()) {
        std::cerr << "uso: solve --algo <i1|vnd|grasp|rgrasp|tabu> --instance <path> "
                     "[--seed N] [--budget-ms M] [--max-no-improve K] [--out file.sol] [--print-cost]\n";
        return 2;
    }

    try {
        const Instance inst = parse_instance(inst_path);
        DistanceMatrix dm(inst);
        const int N = static_cast<int>(inst.size());
        if (args.has("dist-matrix")) dm.load_distance(read_matrix(args.get("dist-matrix"), N));
        if (args.has("time-matrix")) dm.load_time(read_matrix(args.get("time-matrix"), N));
        const Evaluator ev(inst, dm);

        Logger log;
        if (args.has("snapshots"))
            log.enable_snapshots(args.get("snapshots"), static_cast<int>(args.getl("snapshot-stride", 1)));

        const auto t0 = std::chrono::steady_clock::now();
        Solution sol;
        long iters = 0;   // metaheuristic iterations actually run (0 for the deterministic methods)
        if (algo == "i1") {
            sol = solomon_i1(inst, dm);
        } else if (algo == "vnd") {
            VndConfig cfg;
            cfg.first_improvement = args.has("first-improvement");
            if (args.has("neighborhoods")) cfg.order = parse_neighborhoods(args.get("neighborhoods"));
            sol = vnd_local_search(inst, dm, solomon_i1(inst, dm), cfg, &log);
        } else if (algo == "grasp" || algo == "rgrasp") {
            StoppingCriterion stop(args.getl("budget-ms", 5000));
            Rng rng(make_seed(static_cast<std::uint64_t>(args.getl("seed", 1)), inst.name, 0));
            GraspConfig cfg;
            cfg.reactive = (algo == "rgrasp");
            if (!cfg.reactive && args.has("alpha")) cfg.alpha = std::stod(args.get("alpha"));
            if (cfg.reactive) {
                if (args.has("delta")) cfg.delta = std::stod(args.get("delta"));
                if (args.has("block")) cfg.block = static_cast<int>(args.getl("block", 50));
            }
            if (args.has("max-iters")) cfg.max_iters = static_cast<int>(args.getl("max-iters", -1));
            if (args.has("max-no-improve")) cfg.max_no_improve = static_cast<int>(args.getl("max-no-improve", -1));
            if (args.has("neighborhoods")) cfg.vnd.order = parse_neighborhoods(args.get("neighborhoods"));
            if (args.has("target")) cfg.target = std::stod(args.get("target"));
            int gi = 0;
            sol = grasp(inst, dm, stop, rng, cfg, &log, &gi);
            iters = gi;
        } else if (algo == "tabu") {
            StoppingCriterion stop(args.getl("budget-ms", 5000));
            TabuConfig cfg;
            cfg.tenure = static_cast<int>(args.getl("tenure", 15));
            if (args.has("max-iters")) cfg.max_iters = static_cast<int>(args.getl("max-iters", -1));
            if (args.has("max-no-improve")) cfg.max_no_improve = static_cast<int>(args.getl("max-no-improve", -1));
            if (args.has("target")) cfg.target = std::stod(args.get("target"));
            sol = tabu_search(inst, dm, solomon_i1(inst, dm), stop, cfg, &log, &iters);
        } else {
            std::cerr << "algoritmo desconhecido: " << algo << '\n';
            return 2;
        }
        const long ms = static_cast<long>(std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - t0).count());

        if (args.has("trace")) log.write_convergence(args.get("trace"));

        const double dist = Evaluator::round1(ev.primary(sol));
        const int veh = ev.vehicles(sol);
        const ValidationResult vr = validate(inst, dm, sol);

        if (args.has("out")) write_solution(args.get("out"), sol);

        if (args.has("print-cost")) {
            std::cout << std::fixed << std::setprecision(1) << dist << '\n';
        } else if (args.has("csv")) {
            // algo,instance,seed,distance,vehicles,time_ms,feasible,iters
            std::cout << algo << ',' << inst.name << ',' << args.getl("seed", 1) << ','
                      << std::fixed << std::setprecision(1) << dist << ',' << veh << ','
                      << ms << ',' << (vr.feasible ? 1 : 0) << ',' << iters << '\n';
        } else {
            std::cout << "algoritmo : " << algo << '\n'
                      << "instancia : " << inst.name << '\n'
                      << "distancia : " << std::fixed << std::setprecision(1) << dist << '\n'
                      << "veiculos  : " << veh << '\n'
                      << "tempo(ms) : " << ms << '\n'
                      << "viavel    : " << (vr.feasible ? "sim" : "NAO") << '\n';
        }
        return vr.feasible ? 0 : 1;
    } catch (const std::exception& e) {
        std::cerr << "erro: " << e.what() << '\n';
        return 2;
    }
}
