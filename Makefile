.RECIPEPREFIX := >

VENV := $(HOME)/tesis/.venv
PYTHON := $(VENV)/bin/python

WINDOWS_LAYOUT_DIR ?= /mnt/c/Users/olino/Desktop/radix8-layouts

.PHONY: lint model sim sim-fresh formal cover synth hypothesis regression all clean export-layout

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

export-layout:
>@set -e; \
RUN=$$(find asic/radix2/runs -maxdepth 1 -mindepth 1 -type d -name 'RUN_*' | sort | tail -1); \
if [ -z "$$RUN" ]; then \
    echo "ERROR: No LibreLane radix-2 run found."; \
    exit 1; \
fi; \
DEST="$(WINDOWS_LAYOUT_DIR)/radix2"; \
mkdir -p "$$DEST"; \
echo "Using latest run: $$RUN"; \
echo "Export destination: $$DEST"; \
GDS=$$(find "$$RUN/final" -type f -name '*.gds' 2>/dev/null | head -1); \
if [ -z "$$GDS" ]; then \
    GDS=$$(find "$$RUN" -type f -name '*.klayout.gds' | head -1); \
fi; \
if [ -z "$$GDS" ]; then \
    echo "ERROR: No GDS found in $$RUN"; \
    exit 1; \
fi; \
cp "$$GDS" "$$DEST/radix2_divider.gds"; \
find "$$RUN/final" -type f \( \
    -name '*.def' -o \
    -name '*.lef' -o \
    -name '*.odb' -o \
    -name '*.sdc' -o \
    -name '*.spef' \
\) -exec cp {} "$$DEST/" \; 2>/dev/null || true; \
echo; \
echo "Export complete:"; \
ls -lh "$$DEST"

clean:
>PATH="$(VENV)/bin:$$PATH" $(MAKE) -C verification clean
>rm -rf formal/radix2_bmc
>rm -rf formal/radix2_cover
>rm -f results/radix2_generic.json
>rm -f results.xml