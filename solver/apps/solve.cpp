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
#include <algorithm>
#include <cctype>
#include <cmath>
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
        else if (tok == "twooptstar" || tok == "2opt*")  order.push_back(Neighborhood::TwoOptStar);
    }
    return order;
}

// Solomon's I1 parameters (1987, p.257). The article constrains alpha1+alpha2=1,
// so giving only one of them derives the other; giving both inconsistently is an
// error rather than a silent out-of-spec run.
I1Params parse_i1(const Args& a) {
    I1Params p;
    if (a.has("i1-mu"))     p.mu     = std::stod(a.get("i1-mu"));
    if (a.has("i1-lambda")) p.lambda = std::stod(a.get("i1-lambda"));

    const bool has1 = a.has("i1-alpha1"), has2 = a.has("i1-alpha2");
    if (has1) p.alpha1 = std::stod(a.get("i1-alpha1"));
    if (has2) p.alpha2 = std::stod(a.get("i1-alpha2"));
    if (has1 && !has2) p.alpha2 = 1.0 - p.alpha1;
    else if (has2 && !has1) p.alpha1 = 1.0 - p.alpha2;
    if (std::fabs(p.alpha1 + p.alpha2 - 1.0) > 1e-9)
        throw std::runtime_error("Solomon exige alpha1 + alpha2 = 1 (recebido " +
                                 std::to_string(p.alpha1) + " + " + std::to_string(p.alpha2) + ")");

    const std::string seed_rule = a.get("i1-seed", "far");
    if (seed_rule == "deadline")   p.seed = I1Seed::EarliestDeadline;
    else if (seed_rule != "far")   throw std::runtime_error("--i1-seed deve ser 'far' ou 'deadline'");
    p.tie_break_c11     = a.has("i1-tiebreak-c11");
    p.c12_zero_at_end   = a.has("i1-c12-zero-at-end");
    p.seed_tie_farthest = a.has("i1-seed-tie-farthest");
    return p;
}

// Solomon reports results per problem SET (R1, C1, RC1, R2, C2, RC2).
std::string problem_set(const std::string& name) {
    std::string s;
    for (char c : name) {
        if (std::isalpha(static_cast<unsigned char>(c))) s += static_cast<char>(std::toupper(c));
        else { s += c; break; }
    }
    return s;
}

} // namespace

int main(int argc, char** argv) {
    const Args args = parse_args(argc, argv);
    const std::string algo = args.get("algo", "i1");
    const std::string inst_path = args.get("instance");
    if (inst_path.empty()) {
        std::cerr << "uso: solve --algo <i1|vnd|grasp|rgrasp|tabu> --instance <path> "
                     "[--seed N] [--budget-ms M] [--max-no-improve K] [--out file.sol] [--print-cost]\n"
                     "  I1 (Solomon 1987): [--i1-mu F] [--i1-lambda F] [--i1-alpha1 F] [--i1-alpha2 F]\n"
                     "                     [--i1-seed far|deadline] [--i1-tiebreak-c11]\n"
                     "                     [--i1-c12-zero-at-end] [--i1-seed-tie-farthest]\n"
                     "                     [--dist-mode trunc|double]\n"
                     "  saida: [--csv] [--csv-solomon] [--print-cost]\n";
        return 2;
    }

    try {
        const Instance inst = parse_instance(inst_path);
        DistanceMatrix dm(inst);
        const int N = static_cast<int>(inst.size());

        // Numeric convention. Default 'trunc' changes nothing (the constructor
        // already truncates); 'double' replaces the matrix with full precision,
        // which is what Solomon (1987) used -- see DistanceMatrix.hpp.
        const std::string dist_mode = args.get("dist-mode", "trunc");
        if (dist_mode == "double")     dm.load_distance(make_euclid_matrix(inst, false));
        else if (dist_mode != "trunc") throw std::runtime_error("--dist-mode deve ser 'trunc' ou 'double'");

        // an explicit matrix (Digital Twin) still wins over --dist-mode
        if (args.has("dist-matrix")) dm.load_distance(read_matrix(args.get("dist-matrix"), N));
        if (args.has("time-matrix")) dm.load_time(read_matrix(args.get("time-matrix"), N));
        const Evaluator ev(inst, dm);

        Logger log;
        if (args.has("snapshots"))
            log.enable_snapshots(args.get("snapshots"), static_cast<int>(args.getl("snapshot-stride", 1)));

        // Solomon's insertion criterion, shared by I1 and by the GRASP construction
        const I1Params i1p = parse_i1(args);

        const auto t0 = std::chrono::steady_clock::now();
        Solution sol;
        long iters = 0;   // metaheuristic iterations actually run (0 for the deterministic methods)
        if (algo == "i1") {
            sol = solomon_i1(inst, dm, i1p);
        } else if (algo == "vnd") {
            VndConfig cfg;
            cfg.first_improvement = args.has("first-improvement");
            if (args.has("neighborhoods")) cfg.order = parse_neighborhoods(args.get("neighborhoods"));
            sol = vnd_local_search(inst, dm, solomon_i1(inst, dm, i1p), cfg, &log);
        } else if (algo == "grasp" || algo == "rgrasp") {
            StoppingCriterion stop(args.getl("budget-ms", 5000));
            Rng rng(make_seed(static_cast<std::uint64_t>(args.getl("seed", 1)), inst.name));
            GraspConfig cfg;
            cfg.i1 = i1p;
            cfg.reactive = (algo == "rgrasp");
            if (!cfg.reactive && args.has("alpha")) cfg.alpha = std::stod(args.get("alpha"));
            if (cfg.reactive && args.has("delta")) cfg.delta = std::stod(args.get("delta"));
            if (args.has("max-iters")) cfg.max_iters = static_cast<int>(args.getl("max-iters", -1));
            if (args.has("max-no-improve")) cfg.max_no_improve = static_cast<int>(args.getl("max-no-improve", -1));
            if (cfg.reactive) {
                // `block` (Prais & Ribeiro 2000) e o intervalo entre reponderacoes das
                // probabilidades dos alpha. Em iteracoes ABSOLUTAS ele depende da escala
                // do criterio de parada: com block=199 e K=250 a reponderacao ocorre UMA
                // vez por execucao e o mecanismo reativo nao opera (ver
                // docs/verificacao/02-algoritmos-de-melhoria.md). Preferir --block-frac,
                // que fixa o NUMERO de reponderacoes independentemente de K.
                if (args.has("block-frac")) {
                    const double f = std::stod(args.get("block-frac"));
                    if (f <= 0.0 || f > 1.0) throw std::runtime_error("--block-frac deve estar em (0,1]");
                    if (cfg.max_no_improve <= 0)
                        throw std::runtime_error("--block-frac exige --max-no-improve (o K de referencia)");
                    cfg.block = std::max(1, static_cast<int>(std::lround(f * cfg.max_no_improve)));
                } else if (args.has("block")) {
                    cfg.block = static_cast<int>(args.getl("block", 50));
                }
            }
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
            sol = tabu_search(inst, dm, solomon_i1(inst, dm, i1p), stop, cfg, &log, &iters);
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
        } else if (args.has("csv-solomon")) {
            // One row per (instance, configuration): the four quantities Solomon
            // reports in Tables I-VI, plus the configuration that produced them.
            std::cout << inst.name << ',' << problem_set(inst.name) << ','
                      << args.get("dist-mode", "trunc") << ','
                      << i1p.mu << ',' << i1p.lambda << ','
                      << i1p.alpha1 << ',' << i1p.alpha2 << ','
                      << (i1p.seed == I1Seed::EarliestDeadline ? "deadline" : "far") << ','
                      << (i1p.tie_break_c11 ? 1 : 0) << ','
                      << vr.vehicles << ',' << std::fixed << std::setprecision(4)
                      << vr.schedule_time << ',' << vr.distance << ','
                      << vr.waiting_time << ',' << vr.service_time << ','
                      << ms << ',' << (vr.feasible ? 1 : 0) << '\n';
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
