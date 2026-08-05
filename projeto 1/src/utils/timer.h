#pragma once

#include <chrono>

namespace vrptw {

class Timer {
 public:
  Timer() : start_(Clock::now()) {}
  double elapsedSeconds() const {
    using Sec = std::chrono::duration<double>;
    return std::chrono::duration_cast<Sec>(Clock::now() - start_).count();
  }

 private:
  using Clock = std::chrono::steady_clock;
  Clock::time_point start_;
};

}  // namespace vrptw

