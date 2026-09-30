"""Audit unique completed games and an irreversible failure of the frozen gate."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    selector = json.loads((HERE/'selector_manifest.json').read_text())
    raw = [json.loads(line) for line in (HERE/'pilot.jsonl').read_text(encoding='utf-8').splitlines()]
    fields = ('path','opponent','candidate_sha256','plan_sha256','candidate_reward','opponent_reward',
              'result','frames','candidate_status','opponent_status','candidate_errors','opponent_errors',
              'candidate_telemetry','candidate_capture','configuration_seed_visible')
    unique, duplicates = {}, []
    plan_sha = hashlib.sha256((HERE/'NATIVE_PLAN.md').read_bytes()).hexdigest()
    for row in raw:
        key = (row['version'],row['rival'],row['seed'],row['candidate_seat'])
        assert row['seed'] in range(2908000,2908008) and row['candidate_seat'] in (0,1)
        assert row['version'] in ('old','new') and row['rival'] in ('4ee','v43','market')
        assert row['plan_sha256']==plan_sha
        expected = selector['candidate_sha256'] if row['version']=='new' else '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
        assert row['candidate_sha256']==expected
        if key in unique:
            assert all(row[field]==unique[key][field] for field in fields)
            duplicates.append(key)
        else:
            unique[key]=row
    rows=list(unique.values())
    point=lambda rs:sum(1 if r['result']=='win' else .5 if r['result']=='draw' else 0 for r in rs)
    summaries, failures = {}, []
    for ref in ('4ee','v43','market'):
        versions={v:[r for r in rows if r['rival']==ref and r['version']==v] for v in ('old','new')}
        summaries[ref]={v:{'completed':len(rs),'win_points':point(rs),
                           'WDL':[sum(r['result']==outcome for r in rs) for outcome in ('win','draw','loss')]}
                        for v,rs in versions.items()}
        ceiling=point(versions['new'])+16-len(versions['new'])
        if ceiling<point(versions['old']):
            failures.append(dict(reference=ref,candidate_max_final_win_points=ceiling,
                                 incumbent_win_points_already=point(versions['old'])))
    assert failures, 'Do not claim an irreversible failure without a mathematical bound'
    result=dict(phase='pilot',complete=False,terminated=True,passed=False,rejected=True,
                reason='Frozen reference-specific nonregression gate is impossible even if every unplayed candidate game wins.',
                candidate_sha256=selector['candidate_sha256'],plan_sha256=plan_sha,
                intended_games=96,game_count=len(rows),raw_checkpoint_rows=len(raw),
                duplicate_checkpoint_rows=len(duplicates),duplicate_semantic_results_agree=True,
                duplicate_note='Repeated keys are retained in raw checkpoint but counted once; provenance of duplicate execution is unconfirmed.',
                irreversible_failures=failures,scores=summaries,
                all_completed_games_done=all(r['frames']==720 and r['candidate_status']==r['opponent_status']=='DONE' for r in rows),
                no_recorded_errors=all(not r['candidate_errors'] and not r['opponent_errors'] for r in rows),
                audited_at_utc=datetime.now(timezone.utc).isoformat(),games=sorted(rows,key=lambda r:(r['seed'],r['rival'],r['version'],r['candidate_seat'])))
    (HERE/'pilot.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='games'},indent=2))


if __name__=='__main__':
    main()
