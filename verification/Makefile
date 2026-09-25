TOPLEVEL_LANG = verilog

SIM ?= verilator

VERILOG_SOURCES = $(abspath ../rtl/radix2_divider.sv)

TOPLEVEL = radix2_divider
COCOTB_TEST_MODULES = test_radix2

COMPILE_ARGS += --sv

export PYTHONPATH := $(abspath ../models):$(PYTHONPATH)

PYTHON_BIN := $(HOME)/tesis/.venv/bin/python

include $(shell $(HOME)/tesis/.venv/bin/cocotb-config --makefiles)/Makefile.sim
