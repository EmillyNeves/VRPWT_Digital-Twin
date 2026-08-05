#include <cctype>
#include <array>
#include <cmath>
#include <cstdio>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <optional>
#include <random>
#include <stdexcept>
#include <sstream>
#include <string>
#include <vector>

#include "core/instance.h"
#include "core/solution.h"
#include "heuristics/neighborhood_descent.h"
#include "heuristics/solomon_i1.h"
#include "heuristics/vnd.h"
#include "metaheuristics/grasp.h"
#include "metaheuristics/tabu.h"
#include "utils/arg_parser.h"
#include "utils/bks.h"
#include "utils/fs.h"
#include "utils/sol_writer.h"
#include "utils/sol_reader.h"
#include "utils/timer.h"
#include "utils/validate.h"

static void printUsage() {
  std::cerr << "Uso:\n"
            << "  vrptw solve --algo <i1|nls|vnd|grasp|tabu> --instance <path> [opcoes]\n\n"
            << "  vrptw validate --instance <path> --solution <path> [opcoes]\n\n"
            << "Opcoes comuns:\n"
            << "  --seed <int>                 (default: 42)\n"
            << "  --out <dir>                  (default: results)\n"
            << "  --bks-dir <dir>              (default: solution)\n"
            << "  --tag <string>               (sufixo para arquivos de saida)\n"
            << "  --objective cost             (default: cost)\n\n"
            << "Core:\n"
            << "  --mu <double>                (fixo em 1.0; outros valores sao rejeitados)\n"
            << "  --eps <double>               (default: 1e-6)\n"
            << "  --k-neighbors <int>          (default: 20)\n"
            << "  --log-stride <int>           (default: 1)\n"
            << "  --time-limit <double>        (segundos; 0 = sem limite)\n\n"
            << "Busca local (nls/vnd/grasp/tabu):\n"
            << "  --vnd-neighborhoods <list>   (default: selected set)\n"
            << "                               nomes: relocate_intra,swap_intra,relocate_inter,or_opt,\n"
            << "                                      swap_inter,two_opt_intra,two_opt_inter(two_opt_star_inter),cross_exchange\n"
            << "                               use 'all' para forcar as 8 vizinhancas\n\n"
            << "NLS (selecao de vizinhancas, sem estrutura VND):\n"
            << "  --nls-restart <0|1>          (default: 0; 0 = sem reinicio ao melhorar)\n\n"
            << "Validate:\n"
            << "  --solution <path>            (.sol no formato DIMACS)\n"
            << "  --format <text|json>         (default: text)\n\n"
            << "GRASP:\n"
            << "  --grasp-mode <fixed|reactive> (default: fixed)\n"
            << "  --alpha <double>             (default: 0.3)\n"
            << "  --reactive-alphas <list>     (default: 0.1,0.2,0.3,0.4,0.5)\n"
            << "  --reactive-update <int>      (default: 25)\n"
            << "  --reactive-gamma <double>    (default: 1.0)\n"
            << "  --max-no-improve <int>       (default: 500; 0 = desativado)\n"
            << "  --max-iters <int>            (default: 10000; 0 = desativado)\n\n"
            << "Tabu:\n"
            << "  --tenure <int>               (default: 15; atalho para tenure fixo)\n"
            << "  --tabu-move-policy <best|first> (default: best)\n"
            << "  --max-no-improve <int>       (default: 500; 0 = desativado)\n"
            << "  --max-iters <int>            (default: 10000; 0 = desativado)\n";
}

static std::string sanitizeTag(std::string s) {
  for (char& ch : s) {
    const bool ok = std::isalnum(static_cast<unsigned char>(ch)) || ch == '-' || ch == '_' || ch == '.';
    if (!ok) ch = '_';
  }
  return s;
}

static std::string trimCopy(const std::string& s) {
  std::size_t b = 0;
  while (b < s.size() && std::isspace(static_cast<unsigned char>(s[b]))) ++b;
  std::size_t e = s.size();
  while (e > b && std::isspace(static_cast<unsigned char>(s[e - 1]))) --e;
  return s.substr(b, e - b);
}

static std::vector<double> parseCsvDoubleList(const std::string& spec, const std::string& optName) {
  std::vector<double> out;
  std::stringstream ss(spec);
  std::string token;
  while (std::getline(ss, token, ',')) {
    token = trimCopy(token);
    if (token.empty()) continue;
    try {
      out.push_back(std::stod(token));
    } catch (...) {
      throw std::runtime_error("Double invalido em --" + optName + ": '" + token + "'");
    }
  }
  return out;
}

static std::string joinPipe(const std::vector<double>& xs, int precision = 3) {
  if (xs.empty()) return "-";
  std::ostringstream oss;
  oss << std::fixed << std::setprecision(precision);
  for (std::size_t i = 0; i < xs.size(); ++i) {
    if (i) oss << "|";
    oss << xs[i];
  }
  return oss.str();
}

static vrptw::GraspMode parseGraspMode(const std::string& s) {
  if (s == "fixed") return vrptw::GraspMode::Fixed;
  if (s == "reactive" || s == "reativo") return vrptw::GraspMode::Reactive;
  throw std::runtime_error("Valor invalido em --grasp-mode (use fixed ou reactive)");
}

static vrptw::TabuMovePolicy parseTabuMovePolicy(const std::string& s) {
  if (s == "best") return vrptw::TabuMovePolicy::Best;
  if (s == "first") return vrptw::TabuMovePolicy::First;
  throw std::runtime_error("Valor invalido em --tabu-move-policy (use best ou first)");
}

static std::string normalizeToken(std::string s) {
  s = trimCopy(s);
  for (char& ch : s) {
    if (ch == '-' || ch == '.') ch = '_';
    ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
  }
  return s;
}

static vrptw::VndNeighborhood parseVndNeighborhoodToken(const std::string& tokenRaw) {
  const std::string token = normalizeToken(tokenRaw);
  if (token == "relocate_intra") return vrptw::VndNeighborhood::RelocateIntra;
  if (token == "swap_intra") return vrptw::VndNeighborhood::SwapIntra;
  if (token == "relocate_inter") return vrptw::VndNeighborhood::RelocateInter;
  if (token == "or_opt") return vrptw::VndNeighborhood::OrOpt;
  if (token == "swap_inter") return vrptw::VndNeighborhood::SwapInter;
  if (token == "two_opt_intra") return vrptw::VndNeighborhood::TwoOptIntra;
  if (token == "two_opt_inter" || token == "two_opt_star_inter") return vrptw::VndNeighborhood::TwoOptInter;
  if (token == "cross_exchange") return vrptw::VndNeighborhood::CrossExchange;
  throw std::runtime_error("Vizinhança VND invalida: '" + tokenRaw + "'");
}

static std::vector<vrptw::VndNeighborhood> allVndNeighborhoods() {
  std::vector<vrptw::VndNeighborhood> out;
  out.reserve(vrptw::kVndNeighborhoodCount);
  for (std::size_t i = 0; i < vrptw::kVndNeighborhoodCount; ++i) {
    out.push_back(static_cast<vrptw::VndNeighborhood>(i));
  }
  return out;
}

static std::vector<vrptw::VndNeighborhood> parseVndNeighborhoodList(const std::optional<std::string>& specOpt) {
  if (!specOpt) return vrptw::selectedNeighborhoodSet();
  const std::string spec = trimCopy(*specOpt);
  if (spec.empty()) return vrptw::selectedNeighborhoodSet();
  if (normalizeToken(spec) == "all") return allVndNeighborhoods();

  std::vector<vrptw::VndNeighborhood> out;
  std::array<bool, vrptw::kVndNeighborhoodCount> seen{};
  std::stringstream ss(spec);
  std::string token;
  while (std::getline(ss, token, ',')) {
    token = trimCopy(token);
    if (token.empty()) continue;
    const vrptw::VndNeighborhood n = parseVndNeighborhoodToken(token);
    const std::size_t idx = static_cast<std::size_t>(n);
    if (!seen[idx]) {
      seen[idx] = true;
      out.push_back(n);
    }
  }
  if (out.empty()) throw std::runtime_error("--vnd-neighborhoods vazio; use nomes ou 'all'");
  return out;
}

static std::string joinVndNeighborhoods(const std::vector<vrptw::VndNeighborhood>& neighborhoods) {
  if (neighborhoods.empty()) return "all";
  std::ostringstream oss;
  for (std::size_t i = 0; i < neighborhoods.size(); ++i) {
    if (i) oss << "|";
    oss << vrptw::vndNeighborhoodName(neighborhoods[i]);
  }
  return oss.str();
}

static std::string jsonEscape(std::string_view s) {
  std::string out;
  out.reserve(s.size());
  for (char c : s) {
    const unsigned char ch = static_cast<unsigned char>(c);
    switch (ch) {
      case '\\':
        out += "\\\\";
        break;
      case '"':
        out += "\\\"";
        break;
      case '\n':
        out += "\\n";
        break;
      case '\r':
        out += "\\r";
        break;
      case '\t':
        out += "\\t";
        break;
      default:
        if (ch < 0x20) {
          char buf[7];
          std::snprintf(buf, sizeof(buf), "\\u%04x", static_cast<unsigned int>(ch));
          out += buf;
        } else {
          out.push_back(c);
        }
    }
  }
  return out;
}

static int runValidate(const vrptw::ParsedArgs& args) {
  const std::string instancePath = vrptw::requireString(args, "instance");
  const std::string solutionPath = vrptw::requireString(args, "solution");
  const std::string bksDir = vrptw::getString(args, "bks-dir").value_or("solution");
  const int kNeighbors = vrptw::getInt(args, "k-neighbors").value_or(20);
  const double eps = vrptw::getDouble(args, "eps").value_or(1e-6);
  const std::string format = vrptw::getString(args, "format").value_or("text");

  auto emitJson = [&](std::string_view instanceName, bool feasible, std::optional<double> cost, std::optional<int> routes,
                      std::optional<double> bksCost, std::optional<double> gap, std::string_view err) {
    std::cout << "{";
    std::cout << "\"instance\":\"" << jsonEscape(instanceName) << "\",";
    std::cout << "\"feasible\":" << (feasible ? "true" : "false") << ",";
    if (cost) {
      std::cout << "\"cost\":" << std::fixed << std::setprecision(10) << *cost << ",";
    } else {
      std::cout << "\"cost\":null,";
    }
    if (routes) {
      std::cout << "\"num_routes\":" << *routes << ",";
    } else {
      std::cout << "\"num_routes\":null,";
    }
    if (bksCost) {
      std::cout << "\"bks_cost\":" << std::fixed << std::setprecision(10) << *bksCost << ",";
    } else {
      std::cout << "\"bks_cost\":null,";
    }
    if (gap) {
      std::cout << "\"gap_pct\":" << std::fixed << std::setprecision(6) << *gap << ",";
    } else {
      std::cout << "\"gap_pct\":null,";
    }
    std::cout << "\"error\":\"" << jsonEscape(err) << "\"";
    std::cout << "}\n";
  };

  try {
    vrptw::Instance inst = vrptw::Instance::readSolomon(instancePath, static_cast<std::size_t>(kNeighbors));

    vrptw::Solution sol;
    std::string parseErr;
    if (!vrptw::readSol(solutionPath, &sol, &parseErr)) {
      if (format == "json") {
        emitJson(inst.name, false, std::nullopt, std::nullopt, std::nullopt, std::nullopt, "Falha ao ler .sol: " + parseErr);
      } else {
        std::cerr << "Falha ao ler .sol: " << parseErr << "\n";
      }
      return 2;
    }

    std::string valErr;
    const bool ok = vrptw::validateSolution(sol, inst, eps, &valErr);

    const std::string bksPath = (std::filesystem::path(bksDir) / (inst.name + ".sol")).string();
    const auto bksCost = vrptw::readBksCost(bksPath);
    const std::optional<double> gap = (ok && bksCost) ? std::optional<double>(((sol.cost / *bksCost) - 1.0) * 100.0) : std::nullopt;

    if (format == "json") {
      emitJson(inst.name, ok, sol.cost, static_cast<int>(sol.numRoutes()), bksCost, gap, ok ? "" : valErr);
    } else {
      if (!ok) {
        std::cout << inst.name << " INFEASIBLE: " << valErr << "\n";
      } else {
        std::cout << inst.name << " OK cost=" << std::fixed << std::setprecision(1) << sol.cost
                  << " routes=" << sol.numRoutes();
        if (bksCost) std::cout << " gap=" << std::setprecision(3) << *gap << "%";
        std::cout << "\n";
      }
    }
    return ok ? 0 : 2;
  } catch (const std::exception& e) {
    if (format == "json") {
      emitJson("UNK", false, std::nullopt, std::nullopt, std::nullopt, std::nullopt, e.what());
      return 1;
    }
    std::cerr << "Erro: " << e.what() << "\n";
    return 1;
  }
}

static int runSolve(const vrptw::ParsedArgs& args) {
    const std::string algo = vrptw::requireString(args, "algo");
    const std::string instancePath = vrptw::requireString(args, "instance");
    const int seed = vrptw::getInt(args, "seed").value_or(42);
    const std::string outDir = vrptw::getString(args, "out").value_or("results");
    const std::string bksDir = vrptw::getString(args, "bks-dir").value_or("solution");
    const std::string objective = vrptw::getString(args, "objective").value_or("cost");
    const int kNeighbors = vrptw::getInt(args, "k-neighbors").value_or(20);
    const std::string tag = sanitizeTag(vrptw::getString(args, "tag").value_or(""));

    if (objective != "cost") {
      throw std::runtime_error("Somente --objective cost esta implementado (pedido: " + objective + ")");
    }

    vrptw::Timer timer;
    vrptw::Instance inst = vrptw::Instance::readSolomon(instancePath, static_cast<std::size_t>(kNeighbors));

    const std::string bksPath = (std::filesystem::path(bksDir) / (inst.name + ".sol")).string();
    const auto bksCost = vrptw::readBksCost(bksPath);

    std::string base = algo + "_" + inst.name + "_seed" + std::to_string(seed);
    if (!tag.empty()) base += "_" + tag;

    const std::filesystem::path outRoot(outDir);
    vrptw::ensureDir(outRoot / "logs" / "execution");
    vrptw::ensureDir(outRoot / "logs" / "convergence");
    vrptw::ensureDir(outRoot / "logs" / "vnd");
    vrptw::ensureDir(outRoot / "solutions");

    const double muArg = vrptw::getDouble(args, "mu").value_or(1.0);
    if (std::fabs(muArg - 1.0) > 1e-9) {
      throw std::runtime_error("Comparacao alinhada exige --mu fixo em 1.0");
    }

    vrptw::Solution best;
    constexpr double mu = 1.0;
    const double eps = vrptw::getDouble(args, "eps").value_or(1e-6);
    double alpha = 0.3;
    std::string graspModeLabel = "-";
    std::vector<double> reactiveAlphas;
    int reactiveUpdate = 0;
    double reactiveGamma = 0.0;
    int maxNoImprove = vrptw::getInt(args, "max-no-improve").value_or(500);
    int maxIters = vrptw::getInt(args, "max-iters").value_or(10000);
    int logStride = vrptw::getInt(args, "log-stride").value_or(1);
    double timeLimit = vrptw::getDouble(args, "time-limit").value_or(0.0);
    int tenure = vrptw::getInt(args, "tenure").value_or(15);
    int tenureMin = tenure;
    int tenureMax = tenure;
    std::string tabuMovePolicyLabel = "-";
    std::string tabuTenureModeLabel = "-";
    std::string vndNeighborhoodsLabel = "-";
    std::string nlsRestartLabel = "-";
    std::vector<vrptw::VndNeighborhood> vndNeighborhoods;
    std::optional<vrptw::VndRunStats> vndStats;
    int itersDone = 0;
    int noImproveEnd = 0;

    const bool algoUsesNeighborhoods = (algo == "nls" || algo == "vnd" || algo == "grasp" || algo == "tabu");
    if (algoUsesNeighborhoods) {
      if (args.kv.contains("vnd-neighborhoods")) {
        vndNeighborhoods = parseVndNeighborhoodList(vrptw::getString(args, "vnd-neighborhoods"));
      } else {
        vndNeighborhoods = vrptw::selectedNeighborhoodSet();
      }
      vndNeighborhoodsLabel = joinVndNeighborhoods(vndNeighborhoods);
    }

    if (algo == "i1") {
      best = vrptw::solomonI1(inst, vrptw::I1Params{.mu = mu, .eps = eps});
    } else if (algo == "nls") {
      const bool nlsRestart = vrptw::getInt(args, "nls-restart").value_or(0) != 0;
      nlsRestartLabel = nlsRestart ? "1" : "0";
      best = vrptw::solomonI1(inst, vrptw::I1Params{.mu = mu, .eps = eps});
      vrptw::VndRunStats st;
      best = vrptw::neighborhoodDescent(
          inst, std::move(best),
          vrptw::NeighborhoodDescentParams{
              .base = vrptw::VndParams{.ls = vrptw::LocalSearchParams{.eps = eps},
                                       .timeLimitSec = timeLimit,
                                       .neighborhoods = vndNeighborhoods},
              .restartOnImprove = nlsRestart,
          },
          &st);
      vndStats = st;
    } else if (algo == "vnd") {
      best = vrptw::solomonI1(inst, vrptw::I1Params{.mu = mu, .eps = eps});
      vrptw::VndRunStats st;
      best = vrptw::vnd(inst, std::move(best),
                        vrptw::VndParams{.ls = vrptw::LocalSearchParams{.eps = eps},
                                         .timeLimitSec = timeLimit,
                                         .neighborhoods = vndNeighborhoods},
                        &st);
      vndStats = st;
    } else if (algo == "grasp") {
      alpha = vrptw::getDouble(args, "alpha").value_or(0.3);
      const std::string graspModeText = vrptw::getString(args, "grasp-mode").value_or("fixed");
      const vrptw::GraspMode graspMode = parseGraspMode(graspModeText);
      graspModeLabel = graspModeText;
      reactiveAlphas = parseCsvDoubleList(vrptw::getString(args, "reactive-alphas").value_or("0.1,0.2,0.3,0.4,0.5"),
                                          "reactive-alphas");
      reactiveUpdate = vrptw::getInt(args, "reactive-update").value_or(25);
      reactiveGamma = vrptw::getDouble(args, "reactive-gamma").value_or(1.0);
      if (reactiveUpdate <= 0) throw std::runtime_error("--reactive-update deve ser >= 1");
      if (reactiveGamma < 0.0) throw std::runtime_error("--reactive-gamma deve ser >= 0");
      if (graspMode == vrptw::GraspMode::Reactive && reactiveAlphas.empty()) {
        throw std::runtime_error("--reactive-alphas nao pode ser vazio em --grasp-mode reactive");
      }
      std::mt19937 rng(static_cast<std::mt19937::result_type>(seed));

      const std::string convPath = (outRoot / "logs" / "convergence" / (base + "_convergence.csv")).string();

      vrptw::GraspRunStats st;
      best = vrptw::grasp(inst, rng,
                          vrptw::GraspParams{.mode = graspMode,
                                             .alpha = alpha,
                                             .reactiveAlphas = reactiveAlphas,
                                             .reactiveUpdate = reactiveUpdate,
                                             .reactiveGamma = reactiveGamma,
                                             .mu = mu,
                                             .maxIters = maxIters,
                                             .maxNoImprove = maxNoImprove,
                                             .eps = eps,
                                             .logStride = logStride,
                                             .timeLimitSec = timeLimit,
                                             .neighborhoods = vndNeighborhoods},
                          &st, convPath);
      itersDone = st.itersDone;
      noImproveEnd = st.noImprove;
    } else if (algo == "tabu") {
      tenure = vrptw::getInt(args, "tenure").value_or(15);
      if (args.kv.contains("tenure-min") || args.kv.contains("tenure-max")) {
        throw std::runtime_error(
            "Tenure dinamico foi desativado neste protocolo. Use apenas --tenure.");
      }
      tenureMin = tenure;
      tenureMax = tenure;
      if (tenure <= 0) {
        throw std::runtime_error("Tabu tenure deve ser >= 1");
      }
      tabuTenureModeLabel = "fixed";
      tabuMovePolicyLabel = vrptw::getString(args, "tabu-move-policy").value_or("best");
      const vrptw::TabuMovePolicy tabuMovePolicy = parseTabuMovePolicy(tabuMovePolicyLabel);

      const std::string convPath = (outRoot / "logs" / "convergence" / (base + "_convergence.csv")).string();

      vrptw::Solution start = vrptw::solomonI1(inst, vrptw::I1Params{.mu = mu, .eps = eps});
      vrptw::TabuRunStats st;
      best = vrptw::tabuSearch(inst, std::move(start),
                               vrptw::TabuParams{.movePolicy = tabuMovePolicy,
                                                 .tenureMin = tenureMin,
                                                 .tenureMax = tenureMax,
                                                 .rngSeed = static_cast<unsigned int>(seed),
                                                 .maxIters = maxIters,
                                                 .maxNoImprove = maxNoImprove,
                                                 .eps = eps,
                                                 .logStride = logStride,
                                                 .timeLimitSec = timeLimit,
                                                 .neighborhoods = vndNeighborhoods},
                               &st, convPath);
      itersDone = st.itersDone;
      noImproveEnd = st.noImprove;
    } else {
      throw std::runtime_error("Algo ainda nao implementado: " + algo);
    }

    const double elapsed = timer.elapsedSeconds();

    std::string valErr;
    if (!vrptw::validateSolution(best, inst, eps, &valErr)) {
      throw std::runtime_error("Solucao infeasible: " + valErr);
    }

    const double gap = bksCost ? ((best.cost / *bksCost) - 1.0) * 100.0 : 0.0;

    const std::string solOutPath = (outRoot / "solutions" / (base + ".sol")).string();
    vrptw::writeSol(best, solOutPath, 1);

    const std::string reactiveAlphasCsv = joinPipe(reactiveAlphas, 3);
    const std::string csvOutPath = (outRoot / "logs" / "execution" / (base + ".csv")).string();
    {
      std::ofstream csv(csvOutPath);
      csv << "instance,algorithm,seed,objective,time_sec,num_routes,cost,bks_cost,gap_pct,mu,alpha,grasp_mode,reactive_alphas,reactive_update,reactive_gamma,tenure,tenure_min,tenure_max,tabu_tenure_mode,tabu_move_policy,vnd_neighborhoods,nls_restart,max_iters,max_no_improve,eps,k_neighbors,iters_done,no_improve_end,time_limit\n";
      csv << inst.name << "," << algo << "," << seed << "," << objective << ",";
      csv << std::fixed << std::setprecision(6) << elapsed << ",";
      csv << best.numRoutes() << ",";
      csv << std::setprecision(10) << best.cost << ",";
      if (bksCost) {
        csv << *bksCost << ",";
        csv << std::setprecision(6) << gap << ",";
      } else {
        csv << ",,";
      }
      csv << std::setprecision(3) << mu << ",";
      csv << std::setprecision(3) << alpha << ",";
      csv << graspModeLabel << ",";
      csv << reactiveAlphasCsv << ",";
      csv << reactiveUpdate << ",";
      csv << std::setprecision(3) << reactiveGamma << ",";
      csv << tenure << ",";
      csv << tenureMin << ",";
      csv << tenureMax << ",";
      csv << tabuTenureModeLabel << ",";
      csv << tabuMovePolicyLabel << ",";
      csv << vndNeighborhoodsLabel << ",";
      csv << nlsRestartLabel << ",";
      csv << maxIters << "," << maxNoImprove << ",";
      csv << std::setprecision(9) << eps << ",";
      csv << kNeighbors << ",";
      csv << itersDone << "," << noImproveEnd << ",";
      csv << std::setprecision(3) << timeLimit << "\n";
    }

    if (vndStats.has_value()) {
      const std::string vndPath = (outRoot / "logs" / "vnd" / (base + "_vnd.csv")).string();
      std::ofstream vndCsv(vndPath);
      vndCsv << "neighborhood,tries,applied,total_cost_delta,total_routes_delta\n";
      for (std::size_t i = 0; i < vrptw::kVndNeighborhoodCount; ++i) {
        const auto& st = vndStats->neighborhoods[i];
        vndCsv << vrptw::vndNeighborhoodName(static_cast<vrptw::VndNeighborhood>(i)) << ","
               << st.tries << ","
               << st.applied << "," << std::fixed << std::setprecision(10) << st.totalCostDelta << ","
               << st.totalRoutesDelta << "\n";
      }
    }

    std::cout << inst.name << " algo=" << algo << " cost=" << std::fixed << std::setprecision(1) << best.cost
              << " routes=" << best.numRoutes() << " time=" << std::setprecision(3) << elapsed << "s";
    if (algo == "tabu") {
      std::cout << " tabu_move_policy=" << tabuMovePolicyLabel;
      std::cout << " tabu_tenure_mode=" << tabuTenureModeLabel;
      std::cout << " tabu_tenure=" << tenureMin;
      if (tenureMin != tenureMax) std::cout << ".." << tenureMax;
    }
    if (algoUsesNeighborhoods) std::cout << " vnd_neighborhoods=" << vndNeighborhoodsLabel;
    if (algo == "nls") std::cout << " nls_restart=" << nlsRestartLabel;
    if (bksCost) std::cout << " gap=" << std::setprecision(3) << gap << "%";
    std::cout << "\n";

    return 0;
}

int main(int argc, char** argv) {
  try {
    vrptw::ParsedArgs args = vrptw::parseArgs(argc, argv);
    if (args.command.empty() || vrptw::hasFlag(args, "help")) {
      printUsage();
      return args.command.empty() ? 1 : 0;
    }

    if (args.command == "solve") return runSolve(args);
    if (args.command == "validate") return runValidate(args);

    throw std::runtime_error("Comando desconhecido: " + args.command);
  } catch (const std::exception& e) {
    std::cerr << "Erro: " << e.what() << "\n";
    printUsage();
    return 1;
  }
}
