#include "vrptw/SolutionIO.hpp"
#include "vrptw/Evaluator.hpp"
#include "vrptw/Util.hpp"
#include <fstream>
#include <stdexcept>
#include <iomanip>

namespace vrptw {

ParsedSolution read_solution_file(const std::string& path) {
    std::ifstream f(path);
    if (!f) throw std::runtime_error("nao foi possivel abrir a solucao: " + path);

    ParsedSolution ps;
    std::string raw;
    while (std::getline(f, raw)) {
        const std::string s = util::strip(raw);
        if (s.empty()) continue;

        if (util::contains(s, "Route") || util::contains(s, "route")) {
            const std::size_t colon = s.find(':');
            if (colon == std::string::npos) continue;
            std::vector<int> route;
            for (const auto& t : util::tokens(s.substr(colon + 1))) {
                try { route.push_back(std::stoi(t)); }
                catch (...) { /* skip non-integer token */ }
            }
            if (!route.empty()) ps.routes.push_back(std::move(route));
        } else if (util::contains(s, "Cost") || util::contains(s, "cost")) {
            const auto tk = util::tokens(s);
            if (!tk.empty()) {
                try { ps.cost = std::stod(tk.back()); }
                catch (...) { /* ignore malformed cost */ }
            }
        } else if (util::contains(s, "Reference")) {
            // Only accept a lone, fully-numeric token after the colon. The other
            // SINTEF files hold prose ("... Springer 2007.", "N/A", a URL), and
            // a loose parse would happily read "2007." as a cost.
            const std::size_t colon = s.find(':');
            if (colon == std::string::npos) continue;
            const auto tk = util::tokens(s.substr(colon + 1));
            if (tk.size() == 1) {
                try {
                    std::size_t used = 0;
                    const double v = std::stod(tk[0], &used);
                    if (used == tk[0].size()) ps.reference = v;   // whole token consumed
                } catch (...) { /* not a number: a real citation */ }
            }
        }
    }
    return ps;
}

Solution to_solution(const ParsedSolution& ps, const Instance& inst, const DistanceMatrix& dm) {
    Solution sol;
    sol.routes.reserve(ps.routes.size());
    for (const auto& seq : ps.routes) {
        Route r;
        r.seq = seq;
        r.recompute(inst, dm);
        sol.routes.push_back(std::move(r));
    }
    (void)inst;
    return sol;
}

void write_solution(const std::string& path, const Solution& s) {
    std::ofstream f(path);
    if (!f) throw std::runtime_error("nao foi possivel escrever a solucao: " + path);
    int k = 1;
    for (const auto& r : s.routes) {
        if (r.empty()) continue;
        f << "Route #" << k++ << ":";
        for (int c : r.seq) f << ' ' << c;
        f << '\n';
    }
    f << "Cost " << std::fixed << std::setprecision(1)
      << Evaluator::round1(s.total_distance()) << '\n';
}

} // namespace vrptw
