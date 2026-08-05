#pragma once

#include <cctype>
#include <cstdlib>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace vrptw {

struct ParsedArgs {
  std::string command;
  std::unordered_map<std::string, std::string> kv;
  std::unordered_set<std::string> flags;
  std::vector<std::string> positionals;
};

inline bool startsWith(std::string_view s, std::string_view prefix) {
  return s.size() >= prefix.size() && s.substr(0, prefix.size()) == prefix;
}

inline ParsedArgs parseArgs(int argc, char** argv) {
  ParsedArgs out;
  if (argc < 2) return out;
  out.command = argv[1];

  for (int i = 2; i < argc; ++i) {
    std::string_view tok(argv[i]);
    if (tok == "-h" || tok == "--help") {
      out.flags.insert("help");
      continue;
    }
    if (!startsWith(tok, "--")) {
      out.positionals.emplace_back(tok);
      continue;
    }

    std::string key(tok.substr(2));
    if (key.empty()) throw std::runtime_error("Flag invalida: '--'");

    if (i + 1 < argc) {
      std::string_view next(argv[i + 1]);
      if (!startsWith(next, "--")) {
        out.kv[std::move(key)] = std::string(next);
        ++i;
        continue;
      }
    }
    out.flags.insert(std::move(key));
  }
  return out;
}

inline bool hasFlag(const ParsedArgs& args, std::string_view name) { return args.flags.contains(std::string(name)); }

inline std::optional<std::string> getString(const ParsedArgs& args, std::string_view name) {
  auto it = args.kv.find(std::string(name));
  if (it == args.kv.end()) return std::nullopt;
  return it->second;
}

inline std::string requireString(const ParsedArgs& args, std::string_view name) {
  auto v = getString(args, name);
  if (!v) throw std::runtime_error("Parametro obrigatorio: --" + std::string(name));
  return *v;
}

inline std::optional<int> getInt(const ParsedArgs& args, std::string_view name) {
  auto v = getString(args, name);
  if (!v) return std::nullopt;
  char* end = nullptr;
  long x = std::strtol(v->c_str(), &end, 10);
  if (end == v->c_str() || *end != '\0') throw std::runtime_error("Inteiro invalido em --" + std::string(name));
  if (x < std::numeric_limits<int>::min() || x > std::numeric_limits<int>::max()) {
    throw std::runtime_error("Inteiro fora do range em --" + std::string(name));
  }
  return static_cast<int>(x);
}

inline int requireInt(const ParsedArgs& args, std::string_view name) {
  auto v = getInt(args, name);
  if (!v) throw std::runtime_error("Parametro obrigatorio: --" + std::string(name));
  return *v;
}

inline std::optional<double> getDouble(const ParsedArgs& args, std::string_view name) {
  auto v = getString(args, name);
  if (!v) return std::nullopt;
  char* end = nullptr;
  double x = std::strtod(v->c_str(), &end);
  if (end == v->c_str() || *end != '\0') throw std::runtime_error("Double invalido em --" + std::string(name));
  return x;
}

inline double requireDouble(const ParsedArgs& args, std::string_view name) {
  auto v = getDouble(args, name);
  if (!v) throw std::runtime_error("Parametro obrigatorio: --" + std::string(name));
  return *v;
}

}  // namespace vrptw
