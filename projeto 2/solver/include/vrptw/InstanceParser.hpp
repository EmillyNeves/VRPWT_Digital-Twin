#pragma once
#include "vrptw/Instance.hpp"
#include <string>

namespace vrptw {

// Parse a Solomon-format instance file. Tolerant of CRLF line endings and
// ragged whitespace columns. Throws std::runtime_error on failure.
Instance parse_instance(const std::string& path);

} // namespace vrptw
