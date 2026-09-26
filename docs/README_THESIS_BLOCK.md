# Radix-n Divider Thesis Project

> Design, verification and ASIC physical implementation of iterative integer dividers, progressing from a verified Radix-2 baseline toward Radix-4 and high-performance Radix-8/SRT.

<!-- RADIX8_THESIS_STATUS_BEGIN -->

## Thesis direction

This repository studies whether the reduction in iteration count obtained by higher radix compensates for the extra quotient-selection, datapath, timing, routing and area complexity.

A digit-recurrence divider can be viewed through

```text
R[j+1] = r * R[j] - q[j+1] * D
```

where `R` is the partial remainder, `r` the radix, `q` the selected quotient digit and `D` the divisor.

For WIDTH=32:

| Architecture | Quotient information / iteration | Approx. iterations |
|---|---:|---:|
| Radix-2 | 1 bit | 32 |
| Radix-4 | 2 bits | 16 |
| Radix-8 | 3 bits | 11 |

The final target is a parameterizable Radix-8 SRT divider. SRT (Sweeney-Robertson-Tocher) uses redundant quotient digits and a quotient-digit-selection mechanism, trading more complex logic per iteration for fewer iterations.

## Current implementation

The verified baseline is `rtl/radix2_divider.sv`, an unsigned restoring Radix-2 divider with `start`, `busy`, `done`, deterministic divide-by-zero handling, quotient/remainder outputs, exact WIDTH-cycle normal-operation latency and a one-cycle completion pulse.

```text
start accepted → busy → WIDTH restoring iterations → quotient/remainder valid → done pulse → idle
```

## Verification stack

```text
SystemVerilog RTL
   │
   ├─ Verible lint
   ├─ Python mathematical model
   ├─ independent bit-accurate Radix-2 model
   ├─ pytest + Hypothesis
   ├─ Verilator + cocotb
   │    ├─ directed corners
   │    ├─ deterministic random
   │    ├─ exact latency
   │    ├─ divide-by-zero protocol
   │    ├─ start-while-busy
   │    ├─ reset-during-operation
   │    └─ functional coverage
   ├─ SymbiYosys + Yosys + Z3
   │    ├─ bounded arithmetic properties
   │    └─ cover reachability
   └─ Yosys generic synthesis
```

Unsigned arithmetic contract:

```text
N = Q*D + R
0 <= R < D
```

The current cocotb baseline is 7/7 tests with 11/11 required functional-coverage bins.

Mutation testing is used to evaluate the verification environment itself. Known injected defects have included comparator-boundary corruption (`>=` → `>`) and a `done`-stuck-high protocol defect. Mutations remain on isolated branches and are never merged into the verified baseline.

## ASIC / physical-design stack

```text
SystemVerilog
   ↓
Yosys
   ↓
SKY130A technology mapping
   ↓
LibreLane Classic
   ↓
OpenROAD
   ├─ floorplan
   ├─ placement
   ├─ timing repair
   ├─ CTS
   ├─ global routing
   ├─ detailed routing
   ├─ RC extraction
   └─ post-PnR STA
   ↓
DRC / LVS / antenna
   ↓
GDSII
   ↓
KLayout
```

Tools currently used include SystemVerilog, Verible, Verilator, cocotb, pytest, Hypothesis, SymbiYosys, Yosys, Z3, LibreLane, OpenROAD, SKY130A, `sky130_fd_sc_hd`, Ciel, Nix and KLayout.

### First physical Radix-2 baseline

The first SKY130 bring-up completed the full LibreLane Classic flow.

- 676 functional mapped standard cells
- ~9331.45 µm² mapped functional-cell area
- 169 sequential cells
- die ≈ 174.32 µm × 185.04 µm
- core ≈ 162.84 µm × 163.20 µm
- initial utilization ≈ 35.1%
- final detailed-routing wire length ≈ 30.7 mm
- ~7461 vias
- 20 ns / 50 MHz bring-up constraint closed with zero setup/hold violations
- final DRC PASS
- final LVS PASS
- final antenna PASS

This does **not** establish `Fmax = 50 MHz`. A controlled clock sweep and custom SDC methodology are still required before final PPA claims.

## Automated HTML reporting

Every instrumented Make target is executed through `scripts/run_stage.py`.

The wrapper automatically:

1. runs the EDA/DV command,
2. mirrors output to the terminal,
3. stores a timestamped raw log,
4. records return code, runtime, Git branch and commit,
5. rebuilds an indexed HTML dashboard,
6. exports the dashboard to Windows.

Local report structure:

```text
reports/
├─ runs/
│  └─ YYYYMMDD-HHMMSS/
│     ├─ summary.json
│     ├─ lint.log
│     ├─ sim_fresh.log
│     ├─ formal.log
│     └─ ...
└─ site/
   ├─ index.html
   ├─ runs/
   └─ results/
```

Windows dashboard:

```text
C:\Users\olino\Desktop\radix8-reports\index.html
```

Linux/WSL path:

```text
/mnt/c/Users/olino/Desktop/radix8-reports/index.html
```

The dashboard indexes run history, stage status, parsed simulation/formal/synthesis/ASIC metrics, raw logs and Markdown result summaries.

## Automated physical-layout export

The latest physical views are exported to:

```text
C:\Users\olino\Desktop\radix8-layouts\radix2\latest
```

and archived by LibreLane run name under:

```text
C:\Users\olino\Desktop\radix8-layouts\radix2\archive\RUN_...
```

The export includes KLayout GDS plus final DEF/ODB/LEF/SDC/SPEF views when available.

## Main commands

```bash
# Full verification gate
make all

# Individual verification stages
make lint
make model
make hypothesis
make sim
make sim-fresh
make formal
make cover
make synth

# Full SKY130 RTL-to-GDS flow
make asic

# Reporting/export
make report
make export-reports
make export-layout
make export-all
make open-reports
make serve-reports
```

`make sim` is for fast iteration. After switching Git branches or mutation branches, use `make sim-fresh` to force a clean Verilator rebuild.

## Running the ASIC flow

`make asic` calls `scripts/run_asic.py`. If `librelane` is already in `PATH`, it runs directly; otherwise it automatically uses the existing `~/eda/librelane` Nix environment.

Expected configuration:

```text
PDK_ROOT=$HOME/.ciel
PDK=sky130A
config=asic/radix2/config.yaml
```

## Experimental methodology

Radix-2, Radix-4 and Radix-8/SRT must ultimately be compared using the same operand width, verification suite, random methodology, functional-coverage goals, PDK, standard-cell library, PVT corners, timing constraints, physical-design flow, power/activity assumptions and result-extraction scripts.

Planned comparison metrics include iteration count, latency, maximum achievable clock frequency, throughput, mapped area, physical area, cell count, routing complexity, wire length, power, area-delay product and energy per operation.

## Repository map

```text
rtl/           synthesizable divider RTL
models/        mathematical and independent algorithmic reference models
verification/  cocotb + pytest/Hypothesis
formal/        SymbiYosys harnesses/configs
synthesis/     generic Yosys scripts
asic/          LibreLane/OpenROAD configuration
fpga/          future hardware proof-of-concept
scripts/       reporting/export/automation helpers
results/       compact, versionable result summaries
reports/       generated local HTML/log history (not versioned)
docs/          study/thesis documentation
```

## Roadmap

```text
DONE  Radix-2 RTL baseline
DONE  mathematical + independent algorithm models
DONE  directed/random/protocol tests
DONE  functional coverage
DONE  Hypothesis
DONE  initial formal BMC + cover
DONE  mutation-testing experiments
DONE  generic synthesis baseline
DONE  first SKY130 RTL-to-GDS baseline

NEXT  custom SDC / physical constraints cleanup
NEXT  Formal Harness v2
NEXT  parameter/width sweeps
NEXT  Radix-4
NEXT  Radix-8 / SRT
NEXT  controlled comparative PPA campaign
NEXT  optional FPGA proof-of-concept
```

## References

Core computer-arithmetic references:

- Milos D. Ercegovac and Tomas Lang — *Digital Arithmetic*
- Behrooz Parhami — *Computer Arithmetic: Algorithms and Hardware Designs*
- Israel Koren — *Computer Arithmetic Algorithms*

Supporting digital-design references:

- David Money Harris and Sarah L. Harris — *Digital Design and Computer Architecture*
- Neil H. E. Weste and David Harris — *CMOS VLSI Design*

<!-- RADIX8_THESIS_STATUS_END -->
