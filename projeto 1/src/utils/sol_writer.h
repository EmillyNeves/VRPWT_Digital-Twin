#pragma once

#include <string>

namespace vrptw {

struct Solution;

void writeSol(const Solution& sol, const std::string& path, int precision = 1);

}  // namespace vrptw

