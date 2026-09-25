.RECIPEPREFIX := >

VENV := $(HOME)/tesis/.venv
PYTHON := $(VENV)/bin/python

.PHONY: lint model sim formal cover synth all clean

lint:
>verible-verilog-syntax rtl/*.sv
>verible-verilog-lint rtl/*.sv

model:
>$(PYTHON) models/division_reference.py

sim:
>PATH="$(VENV)/bin:$$PATH" $(MAKE) -C verification SIM=verilator

formal:
>cd formal && sby -f radix2.sby bmc

cover:
>cd formal && sby -f radix2.sby cover

synth:
>yosys -s synthesis/radix2.ys

all: lint model sim formal synth

clean:
>PATH="$(VENV)/bin:$$PATH" $(MAKE) -C verification clean
>rm -rf formal/radix2_bmc
>rm -rf formal/radix2_cover
>rm -f results/radix2_generic.json

.PHONY: hypothesis regression

hypothesis:
>PYTHONPATH="$(CURDIR)/models" $(PYTHON) -m pytest -v verification/test_reference_models.py

regression: lint model hypothesis sim formal cover synth
