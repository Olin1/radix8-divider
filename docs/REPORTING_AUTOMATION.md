# Reporting and Windows Export Automation

The reporting stack turns each instrumented Make target into an indexed experiment.

When `make sim`, `make formal`, `make synth`, etc. run, `scripts/run_stage.py` mirrors output to the terminal, stores a timestamped log, records Git branch/commit/runtime/return code, rebuilds the HTML site, and exports the dashboard to Windows.

## Dashboard

Local:

```text
reports/site/index.html
```

Windows:

```text
C:\Users\olino\Desktop\radix8-reports\index.html
```

The dashboard contains run history, stage status, parsed simulation/formal/synthesis/ASIC metrics, raw logs, and rendered `results/*.md` summaries.

A single top-level Make invocation gets one `REPORT_RUN_ID`, so `make all` groups all stages into one experiment.

## Physical export

`make asic` automatically exports successful latest physical views. You can also run:

```bash
make export-layout
make export-reports
make export-all
```

Layouts are copied to:

```text
C:\Users\olino\Desktop\radix8-layouts\radix2\latest
```

and archived under `radix2\archive\RUN_...`.

## Browser

```bash
make open-reports
```

or:

```bash
make serve-reports
```

then open `http://localhost:8000`.

## Git policy

Version scripts, Makefile, README, LibreLane configs, and compact `results/*.md` baselines. Do not version `reports/runs`, `reports/site`, or large `asic/*/runs` trees.
