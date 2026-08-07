# Build do solver VRPTW. Sem dependencias externas (apenas g++ + make).
CXX      ?= g++
# NB: nao use $(abspath ...) aqui — ele trata o argumento como LISTA separada por
# espacos e corrompe o caminho quando o repositorio esta sob um diretorio com
# espaco no nome (ex.: "Area de trabalho"). O $(shell pwd) preserva o caminho.
ROOT     := $(shell cd .. && pwd)
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
