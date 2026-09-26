#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
README=ROOT/'README.md'; BLOCK=ROOT/'docs'/'README_THESIS_BLOCK.md'
START='<!-- RADIX8_THESIS_STATUS_BEGIN -->'; END='<!-- RADIX8_THESIS_STATUS_END -->'
block=BLOCK.read_text(encoding='utf-8'); bs=block.index(START); be=block.index(END)+len(END); replacement=block[bs:be]; header=block[:bs].rstrip()
current=README.read_text(encoding='utf-8') if README.exists() else ''
if START in current and END in current:
    new=current[:current.index(START)].rstrip()+'\n\n'+replacement+'\n'+current[current.index(END)+len(END):].lstrip()
elif not current.strip():
    new=header+'\n\n'+replacement+'\n'
else:
    new=current.rstrip()+'\n\n---\n\n'+replacement+'\n'
README.write_text(new,encoding='utf-8'); print(f'Updated {README}')
