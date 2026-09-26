.RECIPEPREFIX := >

VENV := $(HOME)/tesis/.venv
PYTHON := $(VENV)/bin/python

.PHONY: lint model sim sim-fresh formal cover synth hypothesis regression all clean

lint:
>verible-verilog-syntax rtl/*.sv
>verible-verilog-lint rtl/*.sv

model:
>$(PYTHON) models/division_reference.py

sim:
>PATH="$(VENV)/bin:$$PATH" $(MAKE) -C verification SIM=verilator

sim-fresh:
>PATH="$(VENV)/bin:$$PATH" $(MAKE) -C verification clean
>PATH="$(VENV)/bin:$$PATH" $(MAKE) -C verification SIM=verilator

formal:
>cd formal && sby -f radix2.sby bmc

cover:
>cd formal && sby -f radix2.sby cover

synth:
>yosys -s synthesis/radix2.ys

hypothesis:
>PYTHONPATH="$(CURDIR)/models" $(PYTHON) -m pytest -v verification/test_reference_models.py

regression: lint model hypothesis sim-fresh formal cover synth

all: regression

clean:
>PATH="$(VENV)/bin:$$PATH" $(MAKE) -C verification clean
>rm -rf formal/radix2_bmc
>rm -rf formal/radix2_cover
>rm -f results/radix2_generic.json
>rm -f results.xml