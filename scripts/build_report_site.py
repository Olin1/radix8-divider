#!/usr/bin/env python3
from __future__ import annotations
import html, json, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = Path(os.environ.get('REPORT_ROOT', ROOT/'reports'))
RUNS = REPORT_ROOT/'runs'
SITE = REPORT_ROOT/'site'
PLAN = json.loads((ROOT/'docs'/'test_plan.json').read_text(encoding='utf-8'))
GUIDE = json.loads((ROOT/'docs'/'stage_guide.json').read_text(encoding='utf-8'))
ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')

CSS = r'''
:root{color-scheme:dark;--bg:#07101f;--panel:#111a2c;--panel2:#172238;--line:#2a3b59;--text:#e8eef8;--muted:#9fb0c8;--cyan:#22d3ee;--green:#34d399;--red:#fb7185;--amber:#fbbf24}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(180deg,#06101e,#09111f 28rem);color:var(--text);font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}a{color:var(--cyan);text-decoration:none}a:hover{text-decoration:underline}header{padding:1.7rem max(4vw,1.2rem);border-bottom:1px solid var(--line);background:rgba(6,16,30,.94);position:sticky;top:0;z-index:5;backdrop-filter:blur(10px)}header h1{margin:0;font-size:clamp(1.45rem,3vw,2.3rem)}header p{margin:.35rem 0 0;color:var(--muted)}nav{display:flex;gap:1rem;flex-wrap:wrap;margin-top:.75rem}main{max-width:1360px;margin:0 auto;padding:1.4rem}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:1rem}.two{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.card{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:14px;padding:1rem;box-shadow:0 10px 30px #0003}.card h3{margin:.15rem 0 .55rem}.status{display:inline-block;font-weight:800;padding:.15rem .5rem;border-radius:999px;font-size:.78rem}.pass{color:var(--green);border:1px solid #34d39966;background:#34d39918}.fail{color:var(--red);border:1px solid #fb718566;background:#fb718518}.unrun{color:var(--muted);border:1px solid var(--line);background:#ffffff08}.warn{color:var(--amber);border:1px solid #fbbf2466;background:#fbbf2418}.muted{color:var(--muted)}.metric{font-size:1.45rem;font-weight:800}.kv{display:grid;grid-template-columns:max-content 1fr;gap:.3rem 1rem}table{width:100%;border-collapse:collapse;margin:.8rem 0}th,td{border-bottom:1px solid var(--line);padding:.55rem .65rem;text-align:left;vertical-align:top}th{color:#cbd5e1}pre{background:#040914;border:1px solid var(--line);padding:1rem;border-radius:10px;overflow:auto;white-space:pre-wrap;word-break:break-word}code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}h2{margin-top:2rem;border-bottom:1px solid var(--line);padding-bottom:.45rem}.callout{border-left:4px solid var(--cyan);padding:.7rem 1rem;background:#22d3ee0d;border-radius:8px;margin:.8rem 0}.warning{border-left-color:var(--amber)}.success{border-left-color:var(--green)}.danger{border-left-color:var(--red)}details{background:#0b1425;border:1px solid var(--line);border-radius:10px;padding:.7rem 1rem;margin:.65rem 0}summary{cursor:pointer;font-weight:700}.progress{height:10px;background:#0a1322;border:1px solid var(--line);border-radius:999px;overflow:hidden}.progress>span{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--green))}footer{color:var(--muted);padding:2rem 0}@media(max-width:850px){.two{grid-template-columns:1fr}}
'''

def esc(x): return html.escape(str(x))
def badge(s):
    c='pass' if s=='PASS' else 'fail' if s=='FAIL' else 'warn' if s=='SKIP' else 'unrun'
    return f'<span class="status {c}">{esc(s)}</span>'

def page(title, body, prefix=''):
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><link rel="stylesheet" href="{prefix}assets/style.css"></head><body><header><h1>{esc(title)}</h1><nav><a href="{prefix}index.html">Dashboard</a><a href="{prefix}test-plan.html">Test Plan</a><a href="{prefix}methodology.html">Methodology</a></nav></header><main>{body}<footer>Generated from the radix8-divider EDA/DV flow.</footer></main></body></html>'''

def log_text(run_dir, stage):
    p=run_dir/f'{stage}.log'
    return ANSI.sub('',p.read_text(encoding='utf-8',errors='replace')) if p.exists() else ''

def parse_sim(log):
    tests={}
    for m in re.finditer(r'\*\*\s+test_radix2\.([A-Za-z0-9_]+)\s+(PASS|FAIL|SKIP)\s+([0-9.]+)',log):
        tests[m.group(1)]={'status':m.group(2),'time':m.group(3)}
    totals={}
    m=re.search(r'TESTS=(\d+)\s+PASS=(\d+)\s+FAIL=(\d+)\s+SKIP=(\d+)',log)
    if m: totals.update(tests=int(m.group(1)),passed=int(m.group(2)),failed=int(m.group(3)),skipped=int(m.group(4)))
    m=re.search(r'Functional coverage:\s*(\d+)/(\d+)\s*bins',log,re.I)
    if m: totals['coverage']=f'{m.group(1)}/{m.group(2)}'
    m=re.search(r'Covered bins:\s*(.+)',log)
    if m: totals['covered_bins']=[x.strip() for x in m.group(1).split(',')]
    totals['_tests']=tests
    return totals

def parse_model(log):
    rows=[]
    for m in re.finditer(r'(\d+)\s*/\s*(\d+):\s*Q=(\d+)\s+R=(\d+)\s+DBZ=(True|False)',log):
        rows.append({'N':m.group(1),'D':m.group(2),'Q':m.group(3),'R':m.group(4),'DBZ':m.group(5)})
    return {'examples':rows}

def parse_stage(stage, log):
    if stage in ('sim','sim_fresh'): return parse_sim(log)
    if stage=='model': return parse_model(log)
    m={}
    if stage=='hypothesis':
        x=re.search(r'(\d+)\s+passed',log); m['pytest_passed']=int(x.group(1)) if x else 0
        x=re.search(r'(\d+)\s+failed',log); m['pytest_failed']=int(x.group(1)) if x else 0
    elif stage=='formal':
        x=re.findall(r'DONE\s+\((PASS|FAIL),\s*rc=(\d+)\)',log); m['sby_status']=x[-1][0] if x else 'UNKNOWN'
    elif stage=='cover':
        x=re.findall(r'reached cover statement .* step (\d+)',log); m['cover_witnesses']=len(x); m['cover_steps']=[int(v) for v in x]
        y=re.findall(r'DONE\s+\((PASS|FAIL),\s*rc=(\d+)\)',log); m['sby_status']=y[-1][0] if y else 'UNKNOWN'
    elif stage=='synth':
        for key,pat in [('cells',r'Number of cells:\s+(\d+)'),('wires',r'Number of wires:\s+(\d+)'),('wire_bits',r'Number of wire bits:\s+(\d+)')]:
            x=re.findall(pat,log); m[key]=int(x[-1]) if x else None
    elif stage=='asic':
        m['flow_complete']='Flow complete.' in log
        for c in ('Antenna','LVS','DRC'): m[c]='PASS' if re.search(r'\*\s+'+c+r'\s+Passed',log,re.S) else 'UNKNOWN'
        x=re.findall(r'Total wire length\s*=\s*([0-9.]+)\s*um',log); m['wire_length_um']=float(x[-1]) if x else None
        x=re.findall(r'Total number of vias\s*=\s*(\d+)',log); m['vias']=int(x[-1]) if x else None
    return m

def stage_status(run,*names):
    for n in names:
        if n in run.get('stages',{}): return run['stages'][n].get('status','UNRUN')
    return 'UNRUN'

def actual_for_plan(item,run,parsed):
    st=item['stage']; name=item['test_name']
    if st=='simulation':
        for s in ('sim_fresh','sim'):
            if name in parsed.get(s,{}).get('_tests',{}): return parsed[s]['_tests'][name]['status']
        return 'UNRUN'
    if st in ('hypothesis','formal','cover'): return stage_status(run,st)
    if st=='asic': return parsed.get('asic',{}).get(name,'UNRUN')
    return 'UNRUN'

def metric_cards(stage,m):
    vals=[]
    if stage in ('sim','sim_fresh'): vals=[('Tests',m.get('tests','—')),('Passed',m.get('passed','—')),('Failed',m.get('failed','—')),('Functional coverage',m.get('coverage','—'))]
    elif stage=='model': vals=[('Reference examples',len(m.get('examples',[])))]
    elif stage=='hypothesis': vals=[('pytest passed',m.get('pytest_passed','—')),('pytest failed',m.get('pytest_failed','—'))]
    elif stage=='formal': vals=[('SBY',m.get('sby_status','—'))]
    elif stage=='cover': vals=[('SBY',m.get('sby_status','—')),('Cover witnesses',m.get('cover_witnesses','—'))]
    elif stage=='synth': vals=[('Cells',m.get('cells','—')),('Wires',m.get('wires','—')),('Wire bits',m.get('wire_bits','—'))]
    elif stage=='asic': vals=[('Flow','PASS' if m.get('flow_complete') else '—'),('DRC',m.get('DRC','—')),('LVS',m.get('LVS','—')),('Antenna',m.get('Antenna','—')),('Wire',f"{m.get('wire_length_um','—')} µm"),('Vias',m.get('vias','—'))]
    return '<div class="grid">'+''.join(f'<div class="card"><div class="muted">{esc(k)}</div><div class="metric">{esc(v)}</div></div>' for k,v in vals)+'</div>'

def plan_table(items,run=None,parsed=None,full=False):
    rows=[]
    for p in items:
        status=actual_for_plan(p,run,parsed) if run is not None else None
        if full:
            rows.append(f'<tr><td><code>{esc(p["id"])}</code></td><td>{esc(p["stage"])}</td><td><code>{esc(p["test_name"])}</code></td><td>{esc(p["category"])}</td><td>{esc(p["objective"])}</td><td>{esc(p["stimulus"])}</td><td>{esc(p["oracle"])}</td><td>{esc(p["pass_criteria"])}</td><td>{esc(p["failure_indicates"])}</td></tr>')
        else:
            rows.append(f'<tr><td><code>{esc(p["id"])}</code></td><td>{esc(p["stage"])}</td><td><code>{esc(p["test_name"])}</code></td><td>{badge(status)}</td><td>{esc(p["objective"])}</td><td>{esc(p["why_it_matters"])}</td></tr>')
    if full:
        head='<tr><th>ID</th><th>Stage</th><th>Test/check</th><th>Type</th><th>Objective</th><th>Stimulus</th><th>Oracle</th><th>Pass criteria</th><th>Failure means</th></tr>'
    else:
        head='<tr><th>ID</th><th>Layer</th><th>Test/check</th><th>Result</th><th>Objective</th><th>Why it matters</th></tr>'
    return '<table>'+head+''.join(rows)+'</table>'

def build():
    SITE.mkdir(parents=True,exist_ok=True); (SITE/'assets').mkdir(exist_ok=True)
    (SITE/'assets'/'style.css').write_text(CSS,encoding='utf-8')
    runs=[]
    if RUNS.exists():
        for d in sorted([p for p in RUNS.iterdir() if p.is_dir()],reverse=True):
            sp=d/'summary.json'
            if sp.exists():
                try:
                    r=json.loads(sp.read_text(encoding='utf-8')); r['_dir']=d; runs.append(r)
                except Exception: pass

    # Test-plan page
    goals=''.join(f'<li>{esc(g)}</li>' for g in PLAN['goals'])
    tpb=f'<section class="card"><h2>Verification intent</h2><ul>{goals}</ul></section><section><h2>Complete indexed test plan</h2>{plan_table(PLAN["tests"],full=True)}</section>'
    (SITE/'test-plan.html').write_text(page('Radix-n Verification Test Plan',tpb),encoding='utf-8')

    # Methodology page
    cards=[]
    for _,g in GUIDE.items():
        qs=''.join(f'<li>{esc(q)}</li>' for q in g.get('questions',[]))
        cards.append(f'<div class="card"><h3>{esc(g["title"])}</h3><p>{esc(g["purpose"])}</p><p><strong>PASS means:</strong> {esc(g["pass_means"])}</p><p><strong>PASS does not mean:</strong> {esc(g["does_not_mean"])}</p><details><summary>Questions to ask</summary><ul>{qs}</ul></details></div>')
    mb='<div class="callout"><strong>Evidence layers.</strong> Lint, reference validation, simulation, formal, synthesis and physical signoff answer different questions. A green stage is meaningful only inside its scope.</div><section><h2>How to interpret each stage</h2><div class="grid">'+''.join(cards)+'</div></section>'
    (SITE/'methodology.html').write_text(page('How to Interpret the EDA/DV Flow',mb),encoding='utf-8')

    runroot=SITE/'runs'; runroot.mkdir(exist_ok=True)
    for run in runs:
        rd=run['_dir']; parsed={st:parse_stage(st,log_text(rd,st)) for st in run.get('stages',{})}
        od=runroot/run['run_id']; od.mkdir(parents=True,exist_ok=True)
        stage_cards=[]
        for st,info in run.get('stages',{}).items():
            g=GUIDE.get(st,{}); m=parsed.get(st,{}); status=info.get('status','UNRUN'); log=log_text(rd,st)
            stage_cards.append(f'<div class="card">{badge(status)}<h3><a href="{esc(st)}.html">{esc(g.get("title",st))}</a></h3><p>{esc(g.get("purpose",""))}</p><div class="muted">{esc(info.get("duration_seconds"))} s</div></div>')
            interpretation=f'<div class="callout success"><strong>What PASS means.</strong> {esc(g.get("pass_means",""))}</div><div class="callout warning"><strong>What PASS does not mean.</strong> {esc(g.get("does_not_mean",""))}</div>' if status=='PASS' else f'<div class="callout danger"><strong>Stage failed.</strong> Debug this layer before relying on downstream evidence.</div>'
            stage_items=[]
            if st in ('sim','sim_fresh'): stage_items=[p for p in PLAN['tests'] if p['stage']=='simulation']
            elif st in ('hypothesis','formal','cover','asic'): stage_items=[p for p in PLAN['tests'] if p['stage']==st]
            details=''
            if stage_items:
                details='<section><h2>Tests/checks represented by this stage</h2>'+plan_table(stage_items,run,parsed)+'</section>'
            if st=='model' and m.get('examples'):
                rows=''.join(f'<tr><td>{x["N"]}</td><td>{x["D"]}</td><td>{x["Q"]}</td><td>{x["R"]}</td><td>{x["DBZ"]}</td></tr>' for x in m['examples'])
                details+='<section><h2>Reference-model sanity examples</h2><table><tr><th>N</th><th>D</th><th>Q</th><th>R</th><th>DBZ</th></tr>'+rows+'</table><div class="callout">These examples validate the executable oracle path; they are not RTL test cases.</div></section>'
            qs=''.join(f'<li>{esc(q)}</li>' for q in g.get('questions',[]))
            body=f'<section class="card"><h2>Purpose</h2><p>{esc(g.get("purpose",""))}</p></section>{interpretation}<section><h2>Key results</h2>{metric_cards(st,m)}</section>{details}<section><h2>Reviewer questions</h2><ul>{qs}</ul></section><details><summary>Raw log</summary><pre>{esc(log)}</pre></details>'
            (od/f'{st}.html').write_text(page(f'{run["run_id"]} · {g.get("title",st)}',body,prefix='../../'),encoding='utf-8')

        statuses=[actual_for_plan(p,run,parsed) for p in PLAN['tests']]
        executed=sum(s!='UNRUN' for s in statuses); passed=sum(s=='PASS' for s in statuses); failed=sum(s=='FAIL' for s in statuses)
        pct=round(passed/executed*100,1) if executed else 0
        overview=f'<section class="card"><div class="kv"><strong>Run</strong><span>{esc(run["run_id"])}</span><strong>Branch</strong><span>{esc(run.get("branch"))}</span><strong>Commit</strong><span><code>{esc(run.get("commit_short"))}</code></span><strong>Planned checks executed</strong><span>{executed}/{len(PLAN["tests"])}</span><strong>Passed</strong><span>{passed}</span><strong>Failed</strong><span>{failed}</span></div><div class="progress"><span style="width:{pct}%"></span></div></section>'
        body=overview+'<section><h2>Stages in this Make invocation</h2><div class="grid">'+''.join(stage_cards)+'</div></section><section><h2>Test-plan execution matrix</h2><p class="muted">UNRUN is intentional: it means that check exists in the project plan but this particular Make invocation did not exercise it.</p>'+plan_table(PLAN['tests'],run,parsed)+'</section>'
        (od/'index.html').write_text(page(f'EDA/DV Run {run["run_id"]}',body,prefix='../../'),encoding='utf-8')

    # Result summaries
    rs=SITE/'results'; rs.mkdir(exist_ok=True); links=[]
    if (ROOT/'results').exists():
        for md in sorted((ROOT/'results').glob('*.md')):
            (rs/f'{md.stem}.html').write_text(page(md.name,f'<pre>{esc(md.read_text(encoding="utf-8",errors="replace"))}</pre>',prefix='../'),encoding='utf-8')
            links.append(f'<li><a href="results/{esc(md.stem)}.html">{esc(md.name)}</a></li>')

    latest=runs[0] if runs else None
    if latest:
        rd=latest['_dir']; parsed={st:parse_stage(st,log_text(rd,st)) for st in latest.get('stages',{})}
        sim=parsed.get('sim_fresh') or parsed.get('sim') or {}
        cards=[('Latest run',latest['run_id']),('RTL tests',f'{sim.get("passed","—")}/{sim.get("tests","—")} passed' if sim else 'not run'),('Functional coverage',sim.get('coverage','not run') if sim else 'not run'),('Formal BMC',parsed.get('formal',{}).get('sby_status','not run')),('Formal cover',parsed.get('cover',{}).get('sby_status','not run')),('Generic cells',parsed.get('synth',{}).get('cells','not run')),('Physical DRC',parsed.get('asic',{}).get('DRC','not run')),('Physical LVS',parsed.get('asic',{}).get('LVS','not run'))]
        chtml=''.join(f'<div class="card"><div class="muted">{esc(k)}</div><div class="metric">{esc(v)}</div></div>' for k,v in cards)
        latest_section=f'<section><h2>Latest evidence at a glance</h2><div class="grid">{chtml}</div></section><section><h2>Latest test-plan status</h2>{plan_table(PLAN["tests"],latest,parsed)}</section>'
    else:
        latest_section='<div class="card">No indexed runs yet. Run <code>make all</code>.</div>'

    hist=[]
    for r in runs:
        states=list(r.get('stages',{}).values()); s='FAIL' if any(x.get('status')=='FAIL' for x in states) else ('PASS' if states else 'UNRUN')
        hist.append(f'<tr><td><a href="runs/{esc(r["run_id"])}/index.html">{esc(r["run_id"])}</a></td><td>{esc(r.get("branch"))}</td><td><code>{esc(r.get("commit_short"))}</code></td><td>{badge(s)}</td><td>{len(states)}</td></tr>')

    intro='<section class="card"><h2>What this dashboard is for</h2><p>This is not only a PASS/FAIL log viewer. It indexes the verification plan, the evidence produced by each Make target, the meaning and limitations of each result, and physical-design signoff evidence. Use it to answer: <em>what did we test, why did we test it, what passed, what remains untested, and what conclusion is justified?</em></p></section>'
    body=intro+latest_section+'<section><h2>Core project interpretation</h2><div class="two"><div class="card"><h3>Current proven baseline</h3><p>Unsigned restoring Radix-2 RTL with dynamic verification, reference-model validation, bounded formal checks, generic synthesis and a first SKY130 RTL-to-GDS bring-up.</p></div><div class="card"><h3>Not yet proven</h3><p>Radix-4 and Radix-8/SRT implementations, unbounded formal correctness, final Fmax, and controlled cross-architecture power/PPA comparisons remain future work.</p></div></div></section><section><h2>Indexed result summaries</h2><div class="card"><ul>'+(''.join(links) if links else '<li>No results/*.md summaries found.</li>')+'</ul></div></section><section><h2>Run history</h2><table><tr><th>Run</th><th>Branch</th><th>Commit</th><th>Overall stage status</th><th>Stages</th></tr>'+''.join(hist)+'</table></section>'
    index=f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Radix-n Thesis EDA/DV Dashboard</title><link rel="stylesheet" href="assets/style.css"></head><body><header><h1>Radix-n Divider Thesis · EDA/DV Dashboard</h1><p>Test plan + evidence + interpretation + physical-design results</p><nav><a href="index.html">Dashboard</a><a href="test-plan.html">Test Plan</a><a href="methodology.html">Methodology</a></nav></header><main>{body}<footer>Generated by build_report_site.py</footer></main></body></html>'
    (SITE/'index.html').write_text(index,encoding='utf-8')
    print('Generated',SITE/'index.html')

if __name__=='__main__': build()
