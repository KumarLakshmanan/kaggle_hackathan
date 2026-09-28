from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.physical_route_rollout_20260928.fast_game import play,sha
from diagnostics.local_target_20260928.run_lock import exclusive_run


def game(job):
    variant,fixture,seat,plan_sha=job
    row=play(fixture,variant['candidate'],variant['candidate_sha256'],seat)
    base=next(b for b in fixture['baseline_frozen_tape_both_seat_outcomes'] if b['seat']==seat)
    return dict(row,version=variant['version'],team=fixture['team'],baseline_result=base['result'],
                baseline_margin=base['margin'],plan_sha256=plan_sha)


def main():
    pool=json.loads((HERE/'pool.json').read_text(encoding='utf-8'))
    assert pool['plan_sha256']==sha(HERE/'PLAN.md')
    assert all(v['candidate_sha256']==sha(v['candidate']) for v in pool['variants'])
    checkpoint=HERE/'fast_screen.jsonl'
    rows=[json.loads(s) for s in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    key=lambda r:(r['version'],r['fixture_id'],r['candidate_seat'])
    done={key(r) for r in rows};assert len(done)==len(rows)
    expected={(v['version'],f['fixture_id'],seat):v['candidate_sha256'] for v in pool['variants'] for f in pool['fixtures'] for seat in (0,1)}
    assert all(r['candidate_sha256']==expected[key(r)] and r['plan_sha256']==pool['plan_sha256'] for r in rows)
    jobs=[(v,f,seat,pool['plan_sha256']) for v in pool['variants'] for f in pool['fixtures'] for seat in (0,1)
          if (v['version'],f['fixture_id'],seat) not in done]
    with checkpoint.open('a',encoding='utf-8') as output:
        with ProcessPoolExecutor(max_workers=2) as executor:
            for future in as_completed([executor.submit(game,j) for j in jobs]):
                row=future.result();rows.append(row)
                output.write(json.dumps(row,ensure_ascii=False)+'\n');output.flush()
                print(f'{len(rows)}/20 {row["version"]} {row["team"]} seat{row["candidate_seat"]}: '
                      f'{row["result"]} {row["margin"]:+.0f}, guard {row["candidate_telemetry"]["partial_plant_turns"]}',flush=True)
    assert len(rows)==20
    summaries=[]
    for variant in pool['variants']:
        arm=[r for r in rows if r['version']==variant['version']]
        pairs=[[r for r in arm if r['fixture_id']==f['fixture_id']] for f in pool['fixtures']]
        rescued=[rs[0]['team'] for rs in pairs if all(r['result']=='win' for r in rs) and any(r['baseline_result']!='win' for r in rs)]
        active=all(all(r['candidate_telemetry']['partial_plant_turns']>0 for r in rs)
                   for rs in pairs if rs[0]['team'] in rescued)
        clean=all(r['frames']==720 and r['candidate_status']==r['opponent_status']=='DONE' and not r['candidate_errors'] for r in arm)
        preserved=all(r['result']=='win' for r in arm if r['baseline_result']=='win')
        summaries.append(dict(version=variant['version'],candidate_sha256=variant['candidate_sha256'],
            passed=clean and preserved and bool(rescued) and active,all_clean=clean,preserved=preserved,rescued=rescued,
            win_points=sum(1 if r['result']=='win' else .5 if r['result']=='draw' else 0 for r in arm),
            margin_delta=sum(r['margin']-r['baseline_margin'] for r in arm)))
    eligible=[s for s in summaries if s['passed']]
    selected=sorted(eligible,key=lambda s:(-len(s['rescued']),-s['win_points'],-s['margin_delta'],s['version']))[0]['version'] if eligible else None
    result=dict(complete=True,passed=bool(selected),selected=selected,plan_sha256=pool['plan_sha256'],pool_sha256=sha(HERE/'pool.json'),
                summaries=summaries,games=sorted(rows,key=key))
    (HERE/'fast_screen.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='games'},indent=2,ensure_ascii=False))


if __name__=='__main__':
    with exclusive_run(HERE/'screen.lock'):main()
