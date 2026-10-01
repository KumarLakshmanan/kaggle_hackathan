"""Publish measured results and preserve/promote only a qualified exact candidate."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import random
import shutil

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
BASE_SHA='4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def rows(phase):return [json.loads(s) for s in (HERE/f'{phase}_results.jsonl').read_text().splitlines()]
def points(r):return {'win':1.,'draw':.5,'loss':0.}[r['result']]

def confidence(cases):
    by_seed={}
    for r in cases:
        by_seed.setdefault(r['seed'],{}).setdefault((r['rival'],r['candidate_seat']),{})[r['version']]=r
    blocks=[]
    for seed,pairs in sorted(by_seed.items()):
        assert len(pairs)==8 and all(set(pair)=={'candidate','baseline'} for pair in pairs.values())
        blocks.append(dict(seed=seed,delta=sum(points(pair['candidate'])-points(pair['baseline']) for pair in pairs.values())))
    rng=random.Random(33000000);deltas=[b['delta'] for b in blocks]
    boots=sorted(sum(rng.choice(deltas) for _ in deltas)/(len(deltas)*8) for _ in range(10000))
    return dict(whole_seed_blocks=blocks,point_rate_delta=sum(deltas)/(len(deltas)*8),bootstrap_95pct=[boots[249],boots[9749]])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--promote',action='store_true');args=parser.parse_args()
    candidate=HERE/'candidate_v1.py';manifest=read(candidate.with_suffix('.manifest.json'))
    assert sha(candidate)==manifest['candidate_sha256']
    records={phase:read(HERE/f'{phase}_receipt.json') for phase in ('pilot','top20','top100','confirm') if (HERE/f'{phase}_receipt.json').exists() and read(HERE/f'{phase}_receipt.json').get('complete')}
    for phase,r in records.items():
        assert r['candidate_sha256']==sha(candidate) and r['results_sha256']==sha(HERE/f'{phase}_results.jsonl')
    interval=confidence(rows('confirm')) if 'confirm' in records else None
    loader=read(HERE/'loader_receipt.json') if (HERE/'loader_receipt.json').exists() else None
    engineering=read(HERE/'engineering_checks.json')
    source_binding=(sha(ROOT/'kaggriculture_engine/engine.py')==manifest['engine_sha256'] and
                    sha(ROOT/'kaggriculture_engine/native_core.py')==manifest['simulator_sha256'] and
                    engineering['engine_sha256']==manifest['engine_sha256'] and
                    engineering['core_sha256']==manifest['simulator_sha256'] and
                    sha(HERE/'baseline_4eeac9c3.py')==manifest['baseline_sha256']==BASE_SHA)
    qualified=(source_binding and engineering['passed'] and
               all(p in records for p in ('pilot','top20','top100','confirm')) and
               records['pilot']['assessment']['passed'] and
               all(records[p]['assessment']['point_gain']>=0 and all(g['clean'] for g in records[p]['assessment']['groups'].values()) for p in ('top20','top100')) and
               records['confirm']['assessment']['passed'] and interval['bootstrap_95pct'][0]>0 and
               loader and loader['passed'] and loader['candidate_sha256']==sha(candidate))
    promotion=False
    if args.promote:
        assert qualified,'Frozen promotion gates not passed.'
        assert sha(ROOT/'main.py')==BASE_SHA,'Root main changed; inspect before promotion.'
        backup=ROOT/'main_before_executable_engine_20260930_4eeac9c3.py'
        if not backup.exists():
            with backup.open('xb') as stream:stream.write((ROOT/'main.py').read_bytes())
        assert sha(backup)==BASE_SHA
        shutil.copyfile(candidate,ROOT/'main.py');assert sha(ROOT/'main.py')==sha(candidate)
        promotion=True
    standalone=ROOT/f'main_candidate_executable_engine_20260930_{sha(candidate)[:8]}.py'
    if not standalone.exists():
        with standalone.open('xb') as stream:stream.write(candidate.read_bytes())
    assert sha(standalone)==sha(candidate)
    casepath=HERE/'ALL_CASES.csv'
    import csv
    allcases=[r for phase in records for r in rows(phase)]
    fields=['phase','job_id','version','rival','rank','seed','candidate_seat','result','candidate_reward','opponent_reward','margin','frames','candidate_status','opponent_status','max_candidate_call_seconds','candidate_sha256','changed_turns','nodes']
    with casepath.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for phase in records:
            for r in rows(phase):
                t=r.get('candidate_telemetry',{})
                timing=r.get('candidate_timing') or {}
                peak=r.get('max_candidate_call_seconds',timing.get('max_ms',0)/1000)
                writer.writerow({k:(phase if k=='phase' else t.get('engine_changed_turns',0) if k=='changed_turns' else t.get('engine_nodes',0) if k=='nodes' else peak if k=='max_candidate_call_seconds' else r.get(k,'')) for k in fields})
    root_is_candidate=sha(ROOT/'main.py')==sha(candidate)
    result=dict(candidate=str(candidate),candidate_sha256=sha(candidate),standalone_copy=str(standalone),
                qualified=bool(qualified),root_main_promoted=root_is_candidate,promoted_in_this_run=promotion,root_main_sha256=sha(ROOT/'main.py'),
                engine_source_binding=source_binding,engineering_passed=engineering['passed'],
                confirmation_uncertainty=interval,completed_phases=list(records),kaggle_upload_performed=False,
                evidence={str(HERE/f'{phase}_receipt.json'):sha(HERE/f'{phase}_receipt.json') for phase in records},
                generated_at_utc=datetime.now(timezone.utc).isoformat(),
                caveat='Generated tactical market programs. No universal wins, online rating estimate, or full farm-planning guarantee.')
    for path in (HERE/'candidate_v1.manifest.json',HERE/'engineering_checks.json',HERE/'loader_receipt.json',
                 HERE/'planner_verification.json',HERE/'planner_cli_receipt.json',HERE/'build_safety_receipt.json',
                 HERE/'revisions/build_agent_v1.py'):
        if path.exists():result['evidence'][str(path)]=sha(path)
    (HERE/'DECISION.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    lines=['# Executable search engine — measured results','',
           f'Candidate `{sha(candidate)[:8]}`. Qualified: **{bool(qualified)}**. Promoted to root main.py: **{root_is_candidate}**.',
           '','The online agent generates market programs by reordering, splitting and merging orders with exact native transitions; it retains the existing complete worker schedule. The separate offline physical planner generates movement, transfers, coordinated work and funded investments. Its focused probes pass, but that broader planner is experimental and has not earned competition promotion.',
           '','| Panel | Baseline W/D/L | Candidate W/D/L | Point gain | Candidate mean coin margin | Paired mean margin gain |',
           '|---|---:|---:|---:|---:|---:|']
    for phase,r in records.items():
        a=r['assessment'];b=a['groups']['baseline'];c=a['groups']['candidate']
        lines.append(f"| {phase} | {b['wins']}/{b['draws']}/{b['losses']} | {c['wins']}/{c['draws']}/{c['losses']} | {a['point_gain']:+.1f} | {c['mean_margin']:,.1f} | {c['mean_margin']-b['mean_margin']:+,.1f} |")
    if interval:lines+=['',f"Confirmation point-rate difference: {interval['point_rate_delta']:.4f}; whole-seed95% bootstrap interval: {interval['bootstrap_95pct']}."]
    if 'confirm' in records:
        native=rows('confirm')
        lines+=['','## Every reacting reference','',
                '| Policy | Baseline W/D/L | Candidate W/D/L | Point gain | Paired mean margin gain |',
                '|---|---:|---:|---:|---:|']
        for rival in sorted({r['rival'] for r in native}):
            grouped={v:[r for r in native if r['rival']==rival and r['version']==v] for v in ('baseline','candidate')}
            wdl={v:'/'.join(str(sum(r['result']==outcome for r in cases)) for outcome in ('win','draw','loss')) for v,cases in grouped.items()}
            gain=sum(points(r) for r in grouped['candidate'])-sum(points(r) for r in grouped['baseline'])
            margins={v:sum(r['margin'] for r in cases)/len(cases) for v,cases in grouped.items()}
            lines.append(f"| {rival} | {wdl['baseline']} | {wdl['candidate']} | {gain:+.1f} | {margins['candidate']-margins['baseline']:+,.1f} |")
        peak=max((r.get('candidate_timing') or {}).get('max_ms',0)/1000 for r in native if r['version']=='candidate')
        lines+=['',f'Native confirmation measured peak candidate call: {peak:.6f}s under the six-worker local run. All-case CSV uses nested native timing fields; the generic native receipt field `max_seconds` is zero because that coordinator reads the fast-runner field only. Clean completion is the frozen runtime gate.']
    if loader:lines+=['',f"Native framework/file-loader parity in both seats: **{loader['passed']}**. Same actions/rewards as direct execution; minimum overage: {min(r['minimum_remaining_overage'] for r in loader['rows']):.6f}s."]
    lines+=['','Saved top20/top100 are from the2026-09-29 22:34:23IST snapshot. They repeat recorded opponent actions, cannot react, and are correlated; they do not establish a live win rate. Top20 rows are reused in top100; do not add their counts as independent games.',
            '','Every case, coins, runtime, action-search counts and exact source hashes: [ALL_CASES.csv](ALL_CASES.csv). All100 saved opponents and every paired seat: [TOP100_PAIRED.md](TOP100_PAIRED.md) and [TOP100_PAIRED.csv](TOP100_PAIRED.csv). Per-phase receipts bind the result ledgers. The original pilot runner is archived under `revisions/run_experiment_pilot.py` after adding the predeclared top100 extension to the coordinator.',
            '','Offline planner execution scope: [PLANNER_SCOPE.md](PLANNER_SCOPE.md), [planner_verification.json](planner_verification.json), and the hash-bound four-turn CLI example [planner_cli_receipt.json](planner_cli_receipt.json). Those checks validate generated action execution, not competitive strength or final-season forecasts.',
            '','After qualification, the builder was guarded against wrapping an already-built engine. A rebuild from the preserved4ee executor produces the exact tested candidate bytes; recursive wrapping is rejected before creating a file: [build_safety_receipt.json](build_safety_receipt.json). The original generation builder is preserved under `revisions/build_agent_v1.py` with its manifest-bound hash.',
            '','No Kaggle submission occurred. Promotion, if any, changes the local artifact only. Beating every opponent or reaching top10 is not established.']
    (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
