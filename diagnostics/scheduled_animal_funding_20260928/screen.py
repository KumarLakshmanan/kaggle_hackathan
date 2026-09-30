from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.physical_route_rollout_20260928.fast_game import play,sha
from diagnostics.local_target_20260928.run_lock import exclusive_run


def main():
    manifest_path=ROOT/'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
    assert sha(manifest_path)=='524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
    data=json.loads(manifest_path.read_text(encoding='utf-8'))
    candidate=json.loads((HERE/'candidate.json').read_text())
    assert candidate['plan_sha256']==sha(HERE/'PLAN.md')
    assert candidate['candidate_sha256']==sha(candidate['candidate'])
    fixtures=[f for f in data['current_top20'] if f['team']=='Boey' or f['team'].startswith('Kaggledew')]
    assert len(fixtures)==2
    checkpoint=HERE/'fast_screen.jsonl'
    rows=[json.loads(s) for s in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    key=lambda r:(r['fixture_id'],r['candidate_seat'])
    done={key(r) for r in rows};assert len(done)==len(rows)
    assert all(r['candidate_sha256']==candidate['candidate_sha256'] and r['plan_sha256']==candidate['plan_sha256'] for r in rows)
    with checkpoint.open('a',encoding='utf-8') as output:
        for fixture in fixtures:
            for seat in (0,1):
                if (fixture['fixture_id'],seat) in done:continue
                trace=HERE/(('Boey' if fixture['team']=='Boey' else 'Kaggledew')+f'_seat{seat}.jsonl.gz')
                assert not trace.exists()
                row=play(fixture,candidate['candidate'],candidate['candidate_sha256'],seat,trace)
                base=next(b for b in fixture['baseline_frozen_tape_both_seat_outcomes'] if b['seat']==seat)
                row.update(team=fixture['team'],baseline_result=base['result'],baseline_margin=base['margin'],
                           plan_sha256=candidate['plan_sha256'],trace_path=str(trace),trace_sha256=sha(trace))
                rows.append(row);output.write(json.dumps(row,ensure_ascii=False)+'\n');output.flush()
                print(f'{len(rows)}/4 {row["team"]} seat{seat}: {row["result"]} {row["margin"]:+.0f}, changes {row["candidate_telemetry"]["animal_funding_turns"]}',flush=True)
    assert len(rows)==4
    clean=all(r['frames']==720 and r['candidate_status']==r['opponent_status']=='DONE' and not r['candidate_errors'] for r in rows)
    preserved=all(r['result']=='win' for r in rows if r['baseline_result']=='win')
    rescued=all(r['result']=='win' and r['candidate_telemetry']['animal_funding_turns']>0 for r in rows if r['team']=='Boey')
    result=dict(complete=True,passed=clean and preserved and rescued,all_clean=clean,preserved=preserved,rescued_boey=rescued,
        candidate_sha256=candidate['candidate_sha256'],plan_sha256=candidate['plan_sha256'],games=rows)
    (HERE/'fast_screen.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='games'},indent=2,ensure_ascii=False))


if __name__=='__main__':
    with exclusive_run(HERE/'screen.lock'):main()
