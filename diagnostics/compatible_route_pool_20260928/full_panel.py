"""Verify composition of selected routes across the entire frozen local panel."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import argparse
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.opening_probe_v2_20260928.qualify import play,sha,MANIFEST,MANIFEST_SHA
from diagnostics.compatible_route_pool_20260928.search import SOURCE_SHA
from diagnostics.compatible_route_pool_20260928.complete_controls import GROUPS
from diagnostics.local_target_20260928.run_lock import exclusive_run


def key(row):return row['rival'],row['candidate_seat']


def main(workers):
    selection=json.loads((HERE/'selection.json').read_text(encoding='utf-8'))
    assert selection['complete'] and selection['passed']
    assert sha(selection['candidate'])==selection['candidate_sha256']
    assert sha(ROOT/'main.py')==SOURCE_SHA and sha(MANIFEST)==MANIFEST_SHA
    assert sha(HERE/'CONTROL_FIX.md')==selection['coverage_correction_sha256']
    matrix=json.loads((HERE/'corrected_screen.json').read_text(encoding='utf-8'))
    components={}
    for row in matrix['games']:
        pair=GROUPS[row['group']][0]
        if str(selection['selected_replacements'].get(pair))==row['version']:
            assert key(row) not in components
            components[key(row)]=row
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    jobs=[]
    for fixture in manifest['live_losses']+manifest['current_top20']:
        for seat in (0,1):
            base=next(r for r in fixture['baseline_frozen_tape_both_seat_outcomes'] if r['seat']==seat)
            expected=components.get((fixture['fixture_id'],seat),base)
            jobs.append(dict(version='new',rival=fixture['fixture_id'],team=fixture['team'],
                panel='loss30' if fixture['fixture_id'].startswith('live-') else 'top20',
                seed=int(fixture['seed']),candidate_seat=seat,path=selection['candidate'],candidate_sha256=selection['candidate_sha256'],
                opponent='rawroute:'+fixture['source_action_tape_path'],opponent_action_sha256=fixture['source_opponent_action_sha256'],
                plan_sha256=sha(HERE/'NATIVE_PLAN.md'),selection_sha256=sha(HERE/'selection.json'),
                baseline_result=base['result'],baseline_margin=base['margin'],
                expected_rewards=[expected['candidate_reward'],expected['opponent_reward']]))
    expected_jobs={key(j):j for j in jobs}
    checkpoint=HERE/'full_panel.jsonl'
    rows=[json.loads(s) for s in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    for row in rows:assert all(row[k]==v for k,v in expected_jobs[key(row)].items())
    done={key(r) for r in rows};assert len(done)==len(rows)
    pending=[j for j in jobs if key(j) not in done]
    print(f'Full panel {len(rows)}/100 complete; {len(pending)} pending',flush=True)
    with checkpoint.open('a',encoding='utf-8') as output:
        for start in range(0,len(pending),16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(play,j) for j in pending[start:start+16]]):
                    row=future.result();rows.append(row)
                    output.write(json.dumps(row,ensure_ascii=False)+'\n');output.flush()
                    if len(rows)%8==0:print(f'Full panel {len(rows)}/100 {row["team"]} {row["result"]} {row["margin"]:+.0f}',flush=True)
    assert len(rows)==len({key(r) for r in rows})==100
    all_done=all(r['frames']==720 and r['candidate_status']==r['opponent_status']=='DONE' for r in rows)
    no_errors=all(not r['candidate_errors'] and not r['opponent_errors'] for r in rows)
    parity=all([r['candidate_reward'],r['opponent_reward']]==r['expected_rewards'] for r in rows)
    preserved=all(r['result']=='win' for r in rows if r['baseline_result']=='win')
    summaries=[];new_sweeps=0
    for panel in ('loss30','top20'):
        games=[r for r in rows if r['panel']==panel];pairs={r['rival']:[] for r in games}
        for row in games:pairs[row['rival']].append(row)
        rescued=[rs[0]['team'] for rs in pairs.values() if all(r['result']=='win' for r in rs)
                 and any(r['baseline_result']!='win' for r in rs)]
        new_sweeps+=len(rescued)
        summaries.append(dict(panel=panel,WDL=[sum(r['result']==o for r in games) for o in ('win','draw','loss')],
                              both_seat_wins=sum(all(r['result']=='win' for r in rs) for rs in pairs.values()),rescued=rescued))
    result=dict(complete=True,passed=all_done and no_errors and parity and preserved and new_sweeps>0,
                candidate=selection['candidate'],candidate_sha256=selection['candidate_sha256'],
                plan_sha256=sha(HERE/'NATIVE_PLAN.md'),selection_sha256=sha(HERE/'selection.json'),
                all_done=all_done,no_errors=no_errors,component_reward_parity=parity,incumbent_win_preservation=preserved,
                summaries=summaries,games=sorted(rows,key=key))
    (HERE/'full_panel.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    assert sha(ROOT/'main.py')==SOURCE_SHA
    print(json.dumps({k:v for k,v in result.items() if k!='games'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=4);args=parser.parse_args()
    with exclusive_run(HERE/'full_panel.lock'):main(args.workers)
