SHELL := /bin/bash
.RECIPEPREFIX := >
.NOTPARALLEL:

# -----------------------------------------------------------------------------
# Project / Python environment
# -----------------------------------------------------------------------------

VENV := $(HOME)/tesis/.venv
PYTHON := $(VENV)/bin/python

# Keep the DV toolchain independent from the LibreLane nix-shell environment.
#
# Intended resolution:
#   Python / sby  -> thesis venv
#   Verible       -> ~/.nix-profile/bin
#   Verilator     -> ~/.nix-profile/bin
#   Yosys         -> normal host installation unless explicitly installed
#                    earlier in this PATH.
HOST_TOOL_PATH := $(VENV)/bin:$(HOME)/.nix-profile/bin:/usr/local/bin:/usr/bin:/bin

# -----------------------------------------------------------------------------
# Windows exports
# -----------------------------------------------------------------------------

WINDOWS_LAYOUT_DIR ?= /mnt/c/Users/olino/Desktop/radix8-layouts
WINDOWS_REPORT_DIR ?= /mnt/c/Users/olino/Desktop/radix8-reports

# -----------------------------------------------------------------------------
# Reporting
# -----------------------------------------------------------------------------

REPORT_ROOT ?= $(CURDIR)/reports

# IMPORTANT:
# Use := so the timestamp is evaluated only once for this top-level make.
#
# Therefore:
#
# make all
#
# produces:
#
# reports/runs/<same-run-id>/
#   lint.log
#   model.log
#   hypothesis.log
#   sim_fresh.log
#   formal.log
#   cover.log
#   synth.log
#
ifndef REPORT_RUN_ID
REPORT_RUN_ID := $(shell date +%Y%m%d-%H%M%S)
endif

AUTO_EXPORT_REPORTS ?= 1

export WINDOWS_LAYOUT_DIR
export WINDOWS_REPORT_DIR
export REPORT_ROOT
export REPORT_RUN_ID
export AUTO_EXPORT_REPORTS

RUN_STAGE := $(PYTHON) scripts/run_stage.py --stage

# -----------------------------------------------------------------------------
# Phony targets
# -----------------------------------------------------------------------------

.PHONY: \
	help \
	tool-versions \
	lint \
	model \
	hypothesis \
	sim \
	sim-fresh \
	formal \
	cover \
	synth \
	regression \
	all \
	asic \
	thesis-run \
	report \
	readme \
	export-layout \
	export-reports \
	export-all \
	open-reports \
	serve-reports \
	clean \
	clean-reports

# -----------------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------------

help:
>@printf '%s\n' \
  'Radix-n Divider Thesis Project' \
  '' \
  'Verification / synthesis:' \
  '  make lint           - Verible syntax + lint' \
  '  make model          - run mathematical reference examples' \
  '  make hypothesis     - property-based Python reference verification' \
  '  make sim            - cocotb/Verilator simulation' \
  '  make sim-fresh      - clean + rebuild + cocotb/Verilator simulation' \
  '  make formal         - SymbiYosys bounded model checking' \
  '  make cover          - SymbiYosys cover / reachability' \
  '  make synth          - generic Yosys synthesis' \
  '  make regression     - complete DV verification gate' \
  '  make all            - alias for regression' \
  '' \
  'Physical design:' \
  '  make asic           - run LibreLane SKY130 RTL-to-GDS flow' \
  '  make thesis-run     - complete DV + synthesis + ASIC evidence run' \
  '  make export-layout  - export latest physical views to Windows' \
  '' \
  'Reporting:' \
  '  make report         - rebuild indexed HTML dashboard' \
  '  make export-reports - copy HTML dashboard to Windows' \
  '  make export-all     - export reports and latest physical layout' \
  '  make open-reports   - open Windows HTML dashboard' \
  '  make serve-reports  - serve reports/site at http://localhost:8000' \
  '  make readme         - refresh generated README thesis section' \
  '' \
  'Utilities:' \
  '  make tool-versions  - print normalized EDA/DV tool versions' \
  '  make clean          - clean generated simulation/formal artifacts' \
  '  make clean-reports  - delete local generated report history/site'

# -----------------------------------------------------------------------------
# Toolchain information
# -----------------------------------------------------------------------------

tool-versions:
>@echo "===== NORMALIZED DV TOOLCHAIN ====="
>@echo "HOST_TOOL_PATH=$(HOST_TOOL_PATH)"
>@echo
>@PATH="$(HOST_TOOL_PATH)" python --version || true
>@PATH="$(HOST_TOOL_PATH)" verilator --version || true
>@PATH="$(HOST_TOOL_PATH)" yosys -V || true
>@PATH="$(HOST_TOOL_PATH)" sby --version || true
>@PATH="$(HOST_TOOL_PATH)" verible-verilog-syntax --version || true
>@echo
>@echo "===== PHYSICAL DESIGN ENVIRONMENT ====="
>@echo "PDK_ROOT=$${PDK_ROOT:-$(HOME)/.ciel}"
>@echo "PDK=$${PDK:-sky130A}"
>@command -v klayout || true
>@command -v ciel || true

# -----------------------------------------------------------------------------
# RTL lint
# -----------------------------------------------------------------------------

lint:
>$(RUN_STAGE) lint -- bash -lc ' \
	export PATH="$(HOST_TOOL_PATH)"; \
	verible-verilog-syntax rtl/*.sv && \
	verible-verilog-lint rtl/*.sv \
'

# -----------------------------------------------------------------------------
# Mathematical reference model
# -----------------------------------------------------------------------------

model:
>$(RUN_STAGE) model -- $(PYTHON) models/division_reference.py

# -----------------------------------------------------------------------------
# Property-based reference-model verification
# -----------------------------------------------------------------------------

hypothesis:
>$(RUN_STAGE) hypothesis -- bash -lc ' \
	export PATH="$(HOST_TOOL_PATH)"; \
	export PYTHONPATH="$(CURDIR)/models"; \
	"$(PYTHON)" -m pytest -v verification/test_reference_models.py \
'

# -----------------------------------------------------------------------------
# Dynamic RTL simulation
# -----------------------------------------------------------------------------

# Fast development simulation.
#
# May reuse verification/sim_build when valid.
sim:
>$(RUN_STAGE) sim -- bash -lc ' \
	export PATH="$(HOST_TOOL_PATH)"; \
	$(MAKE) -C verification SIM=verilator \
'

# Milestone / branch-safe simulation.
#
# Always removes sim_build before recompiling, preventing a binary generated
# from another mutation/branch from being reused accidentally.
sim-fresh:
>$(RUN_STAGE) sim_fresh -- bash -lc ' \
	export PATH="$(HOST_TOOL_PATH)"; \
	$(MAKE) -C verification clean && \
	$(MAKE) -C verification SIM=verilator \
'

# -----------------------------------------------------------------------------
# Formal verification
# -----------------------------------------------------------------------------

formal:
>$(RUN_STAGE) formal -- bash -lc ' \
	export PATH="$(HOST_TOOL_PATH)"; \
	cd formal && \
	sby -f radix2.sby bmc \
'

cover:
>$(RUN_STAGE) cover -- bash -lc ' \
	export PATH="$(HOST_TOOL_PATH)"; \
	cd formal && \
	sby -f radix2.sby cover \
'

# -----------------------------------------------------------------------------
# Generic synthesis
# -----------------------------------------------------------------------------

synth:
>$(RUN_STAGE) synth -- bash -lc ' \
	export PATH="$(HOST_TOOL_PATH)"; \
	yosys -s synthesis/radix2.ys \
'

# -----------------------------------------------------------------------------
# Complete functional / DV regression
# -----------------------------------------------------------------------------

# .NOTPARALLEL guarantees the stages execute sequentially.
#
# REPORT_RUN_ID was evaluated once at Make startup, so every stage is stored
# under the same indexed experiment.
regression: lint model hypothesis sim-fresh formal cover synth
>$(PYTHON) scripts/build_report_site.py
>$(PYTHON) scripts/export_artifacts.py --reports

all: regression

# -----------------------------------------------------------------------------
# SKY130 physical design
# -----------------------------------------------------------------------------

# scripts/run_asic.py:
#
# 1. Uses librelane directly if already available.
# 2. Otherwise enters ~/eda/librelane through nix-shell.
# 3. Uses:
#
#       PDK_ROOT=$HOME/.ciel
#       PDK=sky130A
#
# 4. Runs:
#
#       asic/radix2/config.yaml
#
asic:
>$(RUN_STAGE) asic -- $(PYTHON) scripts/run_asic.py

# -----------------------------------------------------------------------------
# Complete thesis evidence run
# -----------------------------------------------------------------------------

# This is the complete evidence package:
#
# lint
#   ↓
# mathematical model
#   ↓
# Hypothesis
#   ↓
# fresh RTL simulation
#   ↓
# formal BMC
#   ↓
# formal cover
#   ↓
# generic synthesis
#   ↓
# SKY130 RTL-to-GDS
#   ↓
# HTML report
#   ↓
# Windows report/layout export
#
# All stages share the same REPORT_RUN_ID.
thesis-run: lint model hypothesis sim-fresh formal cover synth asic
>$(PYTHON) scripts/build_report_site.py
>$(PYTHON) scripts/export_artifacts.py --all

# -----------------------------------------------------------------------------
# Reporting
# -----------------------------------------------------------------------------

report:
>$(PYTHON) scripts/build_report_site.py

readme:
>$(PYTHON) scripts/update_readme.py

# -----------------------------------------------------------------------------
# Windows exports
# -----------------------------------------------------------------------------

export-layout:
>$(PYTHON) scripts/export_artifacts.py --layout

export-reports: report
>$(PYTHON) scripts/export_artifacts.py --reports

export-all: report
>$(PYTHON) scripts/export_artifacts.py --all

# -----------------------------------------------------------------------------
# Open reports in Windows
# -----------------------------------------------------------------------------

# Do not fail the Make target simply because starting the Windows GUI returns
# an unusual status from inside a Nix/WSL shell.
#
# Report generation/export failures still propagate normally through the
# export-reports dependency.
open-reports: export-reports
>@p="$(WINDOWS_REPORT_DIR)/index.html"; \
if [ ! -f "$$p" ]; then \
	echo "ERROR: Missing $$p"; \
	exit 1; \
fi; \
if [ -x /usr/bin/wslpath ]; then \
	win="$$(/usr/bin/wslpath -w "$$p")"; \
else \
	win="$$p"; \
fi; \
ps="/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"; \
if [ -x "$$ps" ]; then \
	"$$ps" -NoProfile -Command "Start-Process '$$win'" >/dev/null 2>&1 || true; \
	echo "Opened: $$win"; \
else \
	echo "Windows launcher unavailable."; \
	echo "Open manually: $$p"; \
fi

# -----------------------------------------------------------------------------
# Local report web server
# -----------------------------------------------------------------------------

serve-reports: report
>$(PYTHON) -m http.server 8000 --directory reports/site

# -----------------------------------------------------------------------------
# Cleaning
# -----------------------------------------------------------------------------

clean:
>PATH="$(HOST_TOOL_PATH)" $(MAKE) -C verification clean
>rm -rf formal/radix2_bmc
>rm -rf formal/radix2_cover
>rm -f results/radix2_generic.json
>rm -f results.xml

# Deliberately does NOT remove results/*.md.
#
# It removes only generated HTML/log history.
clean-reports:
>rm -rf reports/runs
>rm -rf reports/site