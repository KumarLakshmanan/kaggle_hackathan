"""Repair documented control coverage without changing the frozen route pool."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.opening_probe_v2_20260928.qualify import play, sha, MANIFEST, MANIFEST_SHA
from diagnostics.compatible_route_pool_20260928.search import write_candidate, SOURCE_SHA
from diagnostics.local_target_20260928.run_lock import exclusive_run

GROUPS={
    'A':('BRUNCH_SPOT|BRUNCH_SPOT',('DECEM','leave you')),
    'B':('YARN_STORE|FARMERS_MARKET',('Boey','Kaggledew Valley 🏆')),
    'C':('SMOOTHIE_SHOP|ICE_CREAM_SHOP',('Vadim Vasilenko','Yizhou')),
}


def key(row):
    return row['group'],row['version'],row['rival'],row['candidate_seat']


def setup():
    pool=json.loads((HERE/'pool.json').read_text(encoding='utf-8'))
    initial=json.loads((HERE/'screen.json').read_text(encoding='utf-8'))
    assert initial['complete'] and initial['all_done'] and initial['no_errors']
    assert sha(HERE/'pool.json')==initial['pool_sha256']
    assert sha(HERE/'PLAN.md')==pool['plan_sha256']
    assert sha(MANIFEST)==MANIFEST_SHA and sha(ROOT/'main.py')==SOURCE_SHA
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    assessment_path=ROOT/'diagnostics/current_top20_20260927_172258/assessment.json'
    assert sha(assessment_path)=='9d328af8115e27acb45fd4251a1bbc1fde5fda8c793c027b46792a54c04cbeb7'
    assessment=json.loads(assessment_path.read_text(encoding='utf-8'))
    fixtures={}
    for group,(pair,teams) in GROUPS.items():
        fixtures[group]=[f for f in manifest['live_losses']+manifest['current_top20']
                         if (f['fixture_id']=='live-114289228' and group=='A')
                         or (f['fixture_id'].startswith('top20-') and f['team'] in teams)]
        assert len(fixtures[group])==2
        for fixture in fixtures[group]:
            if fixture['fixture_id'].startswith('top20-'):
                records=[r for r in assessment['games'] if r['team']==fixture['team']]
                assert len(records)==2 and all('|'.join(r['candidate_capture']['shops'][:2])==pair for r in records)
    jobs=[]
    for variant in pool['variants']:
        for fixture in fixtures[variant['group']]:
            for seat in (0,1):
                baseline=next(r for r in fixture['baseline_frozen_tape_both_seat_outcomes'] if r['seat']==seat)
                jobs.append(dict(version=variant['route'],group=variant['group'],rival=fixture['fixture_id'],team=fixture['team'],
                    seed=int(fixture['seed']),candidate_seat=seat,path=variant['candidate'],candidate_sha256=variant['candidate_sha256'],
                    opponent='rawroute:'+fixture['source_action_tape_path'],opponent_action_sha256=fixture['source_opponent_action_sha256'],
                    baseline_result=baseline['result'],baseline_margin=baseline['margin'],plan_sha256=pool['plan_sha256']))
    assert len(jobs)==128 and len({key(j) for j in jobs})==128
    return pool,initial,fixtures,jobs


def run(workers):
    pool,initial,fixtures,jobs=setup()
    correction_sha=sha(HERE/'CONTROL_FIX.md')
    old={key(r):r for r in initial['games']}
    missing=[j for j in jobs if key(j) not in old]
    assert len(missing)==44
    checkpoint=HERE/'controls.jsonl'
    rows=[json.loads(s) for s in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    expected={key(j):j for j in missing}
    for row in rows:
        assert all(row[k]==v for k,v in expected[key(row)].items())
        assert row['coverage_correction_sha256']==correction_sha
    complete={key(r) for r in rows}
    assert len(complete)==len(rows)
    pending=[j for j in missing if key(j) not in complete]
    print(f'Missing controls: {len(rows)}/44 complete; {len(pending)} pending',flush=True)
    with checkpoint.open('a',encoding='utf-8') as output:
        for start in range(0,len(pending),16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(play,j) for j in pending[start:start+16]]):
                    row=future.result()
                    row['coverage_correction_sha256']=correction_sha
                    rows.append(row)
                    output.write(json.dumps(row,ensure_ascii=False)+'\n')
                    output.flush()
                    if len(rows)%4==0:print(f'controls {len(rows)}/44 {row["version"]} {row["team"]} {row["result"]} {row["margin"]:+.0f}',flush=True)
    all_rows=initial['games']+rows
    all_keys={key(r):r for r in all_rows}
    assert len(all_keys)==len(all_rows)==172
    relevant=[all_keys[key(j)] for j in jobs]
    assert all(all(r[k]==v for k,v in j.items()) for r,j in zip(relevant,jobs))
    payload=dict(complete=True,game_count=128,retained_raw_game_count=172,
                 excluded_unaffected_control_games=44,pool_sha256=sha(HERE/'pool.json'),
                 coverage_correction_sha256=correction_sha,
                 all_done=all(r['frames']==720 and r['candidate_status']==r['opponent_status']=='DONE' for r in relevant),
                 no_errors=all(not r['candidate_errors'] and not r['opponent_errors'] for r in relevant),
                 groups=GROUPS,games=sorted(relevant,key=key))
    (HERE/'corrected_screen.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in payload.items() if k!='games'},indent=2))


def select():
    pool,initial,fixtures,jobs=setup()
    screen=json.loads((HERE/'corrected_screen.json').read_text(encoding='utf-8'))
    assert screen['complete'] and screen['all_done'] and screen['no_errors']
    assert screen['pool_sha256']==sha(HERE/'pool.json') and screen['coverage_correction_sha256']==sha(HERE/'CONTROL_FIX.md')
    summaries=[]; replacements={}; chosen_groups=[]
    for group,(pair,_) in GROUPS.items():
        original=fixtures[group]
        base_sweeps=sum(all(r['result']=='win' for r in f['baseline_frozen_tape_both_seat_outcomes']) for f in original)
        base_points=sum(1 if r['result']=='win' else .5 if r['result']=='draw' else 0
                        for f in original for r in f['baseline_frozen_tape_both_seat_outcomes'])
        eligible=[]
        for variant in [v for v in pool['variants'] if v['group']==group]:
            rows=[r for r in screen['games'] if r['group']==group and r['version']==variant['route']]
            pairs={r['rival']:[] for r in rows}
            for row in rows:pairs[row['rival']].append(row)
            sweeps=sum(all(r['result']=='win' for r in rs) for rs in pairs.values())
            points=sum(1 if r['result']=='win' else .5 if r['result']=='draw' else 0 for r in rows)
            regressions=sum(r['baseline_result']=='win' and r['result']!='win' for r in rows)
            item=dict(group=group,route=variant['route'],sweeps=sweeps,win_points=points,regressions=regressions,
                      margin_delta=sum(r['margin']-r['baseline_margin'] for r in rows),
                      fixtures=[dict(team=rs[0]['team'],margins=[r['margin'] for r in rs],
                                     both_seat_win=all(r['result']=='win' for r in rs)) for rs in pairs.values()])
            summaries.append(item)
            if regressions==0 and (sweeps,points)>(base_sweeps,base_points):eligible.append(item)
        if eligible:
            best=sorted(eligible,key=lambda r:(-r['sweeps'],-r['win_points'],-r['margin_delta'],r['route']))[0]
            replacements[pair]=int(best['route']);chosen_groups.append(best)
    targets={'DECEM','Boey','Vadim Vasilenko'}
    rescued=[f['team'] for group in chosen_groups for f in group['fixtures'] if f['team'] in targets and f['both_seat_win']]
    result=dict(complete=True,passed=bool(rescued),selected_replacements=replacements,rescued_top20=rescued,
                chosen_groups=chosen_groups,summaries=summaries,plan_sha256=pool['plan_sha256'],
                pool_sha256=sha(HERE/'pool.json'),coverage_correction_sha256=sha(HERE/'CONTROL_FIX.md'),
                screen_sha256=sha(HERE/'corrected_screen.json'))
    if result['passed']:
        source=(ROOT/'main.py').read_bytes();assert hashlib.sha256(source).hexdigest()==SOURCE_SHA
        target=HERE/'candidate_selected.py'
        result['candidate']=str(target);result['candidate_sha256']=write_candidate(source,replacements,target)
    (HERE/'selection.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='summaries'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('run','select'));parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    with exclusive_run(HERE/'control_completion.lock'):
        run(args.workers) if args.phase=='run' else select()
