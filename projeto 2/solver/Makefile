# Build do solver VRPTW. Sem dependencias externas (apenas g++ + make).
CXX      ?= g++
ROOT     := $(abspath $(CURDIR)/..)
CXXFLAGS := -std=c++20 -O2 -Wall -Wextra -Iinclude -DPROJECT_ROOT='"$(ROOT)"' -MMD -MP
BUILD    := build

SRCS := $(wildcard src/*.cpp)
OBJS := $(patsubst src/%.cpp,$(BUILD)/%.o,$(SRCS))
LIB  := $(BUILD)/libvrptw_core.a

TEST_SRCS := $(wildcard tests/*.cpp)

.PHONY: all test clean
all: $(BUILD)/validate $(BUILD)/solve

$(BUILD):
	@mkdir -p $(BUILD)

$(BUILD)/%.o: src/%.cpp | $(BUILD)
	$(CXX) $(CXXFLAGS) -c $< -o $@

$(LIB): $(OBJS)
	ar rcs $@ $^

$(BUILD)/validate: apps/validate.cpp $(LIB) | $(BUILD)
	$(CXX) $(CXXFLAGS) $< $(LIB) -o $@

$(BUILD)/solve: apps/solve.cpp $(LIB) | $(BUILD)
	$(CXX) $(CXXFLAGS) $< $(LIB) -o $@

$(BUILD)/tests: $(TEST_SRCS) $(LIB) | $(BUILD)
	$(CXX) $(CXXFLAGS) -Itests $(TEST_SRCS) $(LIB) -o $@

test: $(BUILD)/tests
	@./$(BUILD)/tests

clean:
	rm -rf $(BUILD)

-include $(wildcard $(BUILD)/*.d)
