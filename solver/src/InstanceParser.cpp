#include "vrptw/InstanceParser.hpp"
#include "vrptw/Util.hpp"
#include <fstream>
#include <stdexcept>
#include <algorithm>

namespace vrptw {

Instance parse_instance(const std::string& path) {
    std::ifstream f(path);
    if (!f) throw std::runtime_error("nao foi possivel abrir a instancia: " + path);

    enum class Sec { None, Vehicle, Customer };
    Instance inst;
    Sec sec = Sec::None;
    bool got_vehicle = false;

    std::string raw;
    while (std::getline(f, raw)) {
        const std::string s = util::strip(raw);
        if (s.empty()) continue;

        if (util::contains(s, "VEHICLE"))  { sec = Sec::Vehicle;  continue; }
        if (util::contains(s, "CUSTOMER")) { sec = Sec::Customer; continue; }
        // skip column-header rows
        if (util::contains(s, "NUMBER") || util::contains(s, "CAPACITY") ||
            util::contains(s, "CUST")   || util::contains(s, "XCOORD")) continue;

        const auto tk = util::tokens(s);

        if (sec == Sec::None) {
            if (inst.name.empty()) inst.name = s;   // first non-empty line is the name
            continue;
        }
        if (sec == Sec::Vehicle && !got_vehicle) {
            if (tk.size() >= 2) {
                inst.vehicles = std::stoi(tk[0]);
                inst.capacity = std::stod(tk[1]);
                got_vehicle = true;
            }
            continue;
        }
        if (sec == Sec::Customer && tk.size() >= 7) {
            Customer c;
            c.id      = std::stoi(tk[0]);
            c.x       = std::stod(tk[1]);
            c.y       = std::stod(tk[2]);
            c.demand  = std::stod(tk[3]);
            c.ready   = std::stod(tk[4]);
            c.due     = std::stod(tk[5]);
            c.service = std::stod(tk[6]);
            inst.nodes.push_back(c);
        }
    }

    if (inst.nodes.empty())
        throw std::runtime_error("instancia sem clientes: " + path);

    // ensure node[0] is the depot regardless of file order
    std::sort(inst.nodes.begin(), inst.nodes.end(),
              [](const Customer& a, const Customer& b) { return a.id < b.id; });
    if (inst.nodes.front().id != 0)
        throw std::runtime_error("deposito (id 0) ausente em: " + path);

    return inst;
}

} // namespace vrptw
