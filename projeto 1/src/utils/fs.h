#pragma once

#include <filesystem>
#include <string>

namespace vrptw {

inline void ensureDir(const std::filesystem::path& p) { std::filesystem::create_directories(p); }

inline std::string joinPath(const std::filesystem::path& a, const std::filesystem::path& b) {
  return (a / b).string();
}

}  // namespace vrptw

