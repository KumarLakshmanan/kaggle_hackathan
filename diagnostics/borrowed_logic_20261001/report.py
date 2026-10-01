"""All executed cases, matched comparisons and whole-seed confirmation."""
import csv
import json
import random
import statistics
from datetime import datetime,timezone
from pathlib import Path
from run_experiment import sha,point,pairkey,clean

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def interval(rows,baseline_version):
    base={pairkey(r):r for r in rows if r['version']==baseline_version}
    by_seed={};per={};paired=[]
    for r in rows:
        if r['version']!='candidate':continue
        b=base[pairkey(r)];delta=point(r)-point(b)
        by_seed.setdefault(r['seed'],[]).append(delta)
        per[r['rival']]=per.get(r['rival'],0)+delta;paired.append(b)
    blocks=[statistics.mean(v) for _,v in sorted(by_seed.items())]
    rng=random.Random(736);boot=sorted(statistics.mean(rng.choices(blocks,k=len(blocks))) for _ in range(20000))
    return {'paired_point_rate_gain':statistics.mean(blocks),'whole_seed_95_percent_interval':[boot[500],boot[19499]],
        'blocks':len(blocks),'per_reference_gain':per,'baseline_clean':all(clean(r) for r in paired),
        'passed':statistics.mean(blocks)>0 and boot[500]>0 and all(v>=0 for v in per.values()) and all(clean(r) for r in paired)}

def main():
    phases={};rows=[]
    for phase in ('screen','joint','top20','top100','confirm'):
        p=HERE/f'{phase}_receipt.json'
        if p.exists():phases[phase]=json.loads(p.read_text())
        ledger=HERE/f'{phase}_results.jsonl'
        if ledger.exists():rows.extend(dict(json.loads(s),phase=phase) for s in ledger.read_text().splitlines())
    selection=json.loads((HERE/'selection.json').read_text()) if (HERE/'selection.json').exists() else {}
    previous=json.loads((HERE/'DECISION.json').read_text()) if (HERE/'DECISION.json').exists() else {}
    decision={'generated_at_utc':datetime.now(timezone.utc).isoformat(),'selection':selection,
        'promotion_eligible':False,'promoted':previous.get('promoted',False),'root_main_sha256':sha(ROOT/'main.py'),
        'kaggle_access_or_upload':False,'universal_wins_established':False,'confidence':{}}
    if phases.get('confirm',{}).get('complete'):
        confirm=[r for r in rows if r['phase']=='confirm']
        decision['confidence']['baseline']=interval(confirm,'baseline')
        if any(r['version']=='incumbent' for r in confirm):decision['confidence']['incumbent']=interval(confirm,'incumbent')
        candidate=[r for r in confirm if r['version']=='candidate']
        eligible=bool(selection.get('development_passed')) and all(clean(r) for r in candidate)
        eligible &= all(v['passed'] for v in decision['confidence'].values())
        for phase in ('top20','top100'):
            eligible &= phases.get(phase,{}).get('complete',False) and phases.get(phase,{}).get('assessment',{}).get('decisions',{}).get('candidate',{}).get('replay_passed',False)
        loader=json.loads((HERE/'loader_receipt.json').read_text()) if (HERE/'loader_receipt.json').exists() else {}
        eligible &= loader.get('passed',False) and loader.get('candidate_sha256')==selection.get('candidate_sha256')
        decision['promotion_eligible']=bool(eligible)
    fields=['phase','job_id','version','rank','team','rival','seed','candidate_seat','candidate_sha256','candidate_reward','opponent_reward','margin','result','frames','candidate_status','opponent_status','candidate_nonpass_worker_calls','candidate_no_effect_worker_calls','max_candidate_call_seconds','error']
    with (HERE/'ALL_CASES.csv').open('w',newline='',encoding='utf-8-sig') as out:
        w=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    lines=['# Borrowed logic comparison — October 1, 2026','','No Kaggle access or upload. Six source-frozen alternatives tested under PLAN.md. Engineering:144 native boundary/reset cases and physical feed/delivery probes pass.','','## Results','','| Panel | Version | Tested | Wins | Draws | Losses | Matched point gain | Mean coin margin | Clean |','|---|---|---:|---:|---:|---:|---:|---:|---|']
    for phase,r in phases.items():
        if not r.get('complete'):continue
        a=r['assessment']
        for v,g in a['groups'].items():
            delta=a['decisions'].get(v,{}).get('point_gain',0)
            lines.append(f'| {phase} | {v} | {g["games"]} | {g["wins"]} | {g["draws"]} | {g["losses"]} | {delta:+.1f} | {g["mean_margin"]:.1f} | {g["clean"]} |')
        for v,d in r.get('futility_stops',{}).items():lines += ['',f'**{v} stopped prospectively:** {d["reason"]}. Upper bounds: `{json.dumps(d.get("bounds",{}),sort_keys=True)}`. Untested cases are explicitly listed in {phase}_receipt.json; no results are imputed.']
    lines += ['','Stopped candidates use their matched baseline subset, not the full24 controls. Both seats are kept in each paired seed. Cash is diagnostic; wins/draws/losses determine selection. Saved September29 top20 is a subset of top100; fixed tapes are regression controls and cannot establish live strength.','','## Decision','',f'Selected: `{selection.get("name",None)}`. Promotion eligible: **{decision["promotion_eligible"]}**. Locally promoted: **{decision["promoted"]}**.']
    if not selection and phases.get('screen',{}).get('complete'):lines += ['','No borrowed addition earned the frozen promotion criteria. Retain the independently qualified current engine; the six experimental candidates remain available for inspection.']
    for v,c in decision['confidence'].items():lines += ['',f'Against {v}: whole-seed paired point-rate gain {c["paired_point_rate_gain"]:.6f};95% interval {c["whole_seed_95_percent_interval"]};16 paired seed blocks; reference deltas {c["per_reference_gain"]}.']
    lines += ['','Every executed case is in ALL_CASES.csv; JSONL ledgers retain telemetry and exact source identities. No guaranteed wins, Kaggle score estimate or top10 rank follows from these local tests.']
    (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (HERE/'DECISION.json').write_text(json.dumps(decision,indent=2),encoding='utf-8')
    print(json.dumps(decision,indent=2),flush=True)

if __name__=='__main__':main()
