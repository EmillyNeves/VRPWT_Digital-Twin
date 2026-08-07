#pragma once
#include <string>
#include <vector>
#include <sstream>
#include <algorithm>

namespace vrptw::util {

// Remove carriage returns (CRLF tolerance) and trim leading/trailing blanks.
inline std::string strip(std::string s) {
    s.erase(std::remove(s.begin(), s.end(), '\r'), s.end());
    const std::size_t a = s.find_first_not_of(" \t");
    if (a == std::string::npos) return "";
    const std::size_t b = s.find_last_not_of(" \t");
    return s.substr(a, b - a + 1);
}

// Split on arbitrary whitespace (handles the ragged columns of Solomon files).
inline std::vector<std::string> tokens(const std::string& s) {
    std::vector<std::string> out;
    std::istringstream is(s);
    std::string w;
    while (is >> w) out.push_back(w);
    return out;
}

inline bool contains(const std::string& s, const char* sub) {
    return s.find(sub) != std::string::npos;
}

} // namespace vrptw::util
