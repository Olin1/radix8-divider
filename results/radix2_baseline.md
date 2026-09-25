# Radix-2 Baseline Results

## Configuration

- Architecture: restoring radix-2 unsigned divider
- WIDTH: 32 bits
- Iterations per normal division: 32
- RTL: SystemVerilog
- Synthesis: Yosys generic technology mapping

## Verification

- Directed/random cocotb tests: PASS
- Protocol tests: PASS
- Functional coverage test: PASS
- Formal BMC depth: 20
- Formal BMC: PASS
- Formal cover: PASS

## Generic Yosys synthesis

- Wires: 167
- Wire bits: 1142
- Cells: 964
- AND: 133
- DFFE: 167
- DFF: 2
- MUX: 441
- NOT: 46
- OR: 107
- XOR: 68

> These are generic Yosys cells and must not be interpreted as
> physical ASIC area. Physical PPA comparison will use the same
> technology, library and constraints for all divider variants.
