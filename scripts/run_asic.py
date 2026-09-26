#!/usr/bin/env python3
from __future__ import annotations
import os, shlex, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'asic'/'radix2'/'config.yaml'
LIBRELANE_REPO=Path.home()/'eda'/'librelane'
env=os.environ.copy(); env.setdefault('PDK_ROOT',str(Path.home()/'.ciel')); env.setdefault('PDK','sky130A')
if not CONFIG.exists(): raise SystemExit(f'Missing LibreLane config: {CONFIG}')
if shutil.which('librelane'):
    raise SystemExit(subprocess.call(['librelane',str(CONFIG)],cwd=ROOT,env=env))
if not LIBRELANE_REPO.exists():
    raise SystemExit('librelane is not in PATH and ~/eda/librelane was not found.')
inner=(f'cd {shlex.quote(str(ROOT))} && export PDK_ROOT={shlex.quote(env["PDK_ROOT"])} && export PDK={shlex.quote(env["PDK"])} && librelane {shlex.quote(str(CONFIG))}')
raise SystemExit(subprocess.call(['nix-shell','--run',inner],cwd=LIBRELANE_REPO,env=env))
