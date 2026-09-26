cd ~/tesis/radix8-divider

python3 - <<'PY'
from pathlib import Path

path = Path("README.md")
marker = "<!-- RADIX8_THESIS_STATUS_BEGIN -->"

section = r'''

<!-- RADIX8_THESIS_STATUS_BEGIN -->

---

# Radix-n Divider Thesis Project

## Project Overview

This repository is an experimental and educational platform for the design,
verification and physical implementation of high-performance digital integer
dividers.

The long-term thesis objective is to design and compare:

- Radix-2
- Radix-4
- Radix-8
- Radix-8 SRT

under a common verification and ASIC implementation methodology.

The intended thesis direction is:

> **Design, optimization and pre-silicon verification of a parameterizable
> high-performance Radix-8 SRT divider using SystemVerilog, verification-driven
> development, formal methods and ASIC physical implementation.**

The project is intentionally being developed incrementally.

The current Radix-2 design acts as the verified reference architecture against
which future Radix-4 and Radix-8 implementations will be compared.

---

# Why Radix-n?

Digital division can be implemented as an iterative digit-recurrence process.

A simplified recurrence can be written as:

```text
R[j+1] = r * R[j] - q[j+1] * D
