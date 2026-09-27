from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game, engine_version

ERROR_KEYS = ('queue_errors', 'quantity_errors', 'mirror_quantity_errors',
              'farmice_errors', 'integration_gate_collisions', 'planned_funding_errors')


def play(job):
    path, digest, route, seat = job
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    game = run_game(path, 'rawroute:'+route['path'], route['seed'], seat, False, 144, {})
    return dict(team=route['team'], team_id=route['team_id'], rank=route['rank'],
                episode_id=route['episode_id'], **game)


if __name__ == '__main__':
    manifest = json.loads((HERE/'build_manifest.json').read_text())
    routes = json.loads((ROOT/'diagnostics/current_top100_20260927_0730/non_swept_routes.json').read_text())
    old = json.loads((ROOT/'diagnostics/current_top100_20260927_0730/assessment.json').read_text())
    lookup = {(g['team_id'],g['candidate_seat']):g for g in old['games']}
    assert not (HERE/'development.json').exists()
    jobs = [(manifest['candidate'],manifest['candidate_sha256'],r,seat) for r in routes for seat in (0,1)]
    assert len(jobs)==46
    out = dict(started_at_utc=datetime.now(timezone.utc).isoformat(),candidate_sha256=manifest['candidate_sha256'],
               engine_version=engine_version,complete=False,games=[])
    def save():
        (HERE/'development.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(play,j) for j in jobs]):
            row = future.result()
            row['old_margin'] = lookup[row['team_id'],row['candidate_seat']]['margin']
            row['margin_delta'] = row['margin']-row['old_margin']
            out['games'].append(row)
            out['games'].sort(key=lambda g:(g['rank'],g['candidate_seat']))
            save()
            print(f"{len(out['games'])}/46 rank={row['rank']} seat={row['candidate_seat']} {row['result']} "
                  f"margin={row['margin']:+.0f} delta={row['margin_delta']:+.0f} "
                  f"funding_turns={(row.get('candidate_telemetry') or {}).get('planned_funding_turns')}",flush=True)
    games=out['games']
    grouped={r['team_id']:[g for g in games if g['team_id']==r['team_id']] for r in routes}
    sweeps=[r for r in routes if all(g['result']=='win' for g in grouped[r['team_id']])]
    top50_sweeps=[r['team'] for r in sweeps if r['rank']<=50]
    lost_wins=[g for g in games if g['old_margin']>0 and g['margin']<=0]
    all_done=all(g['candidate_status']==g['opponent_status']=='DONE' and g['frames']==720 for g in games)
    errors={k:sum((g.get('candidate_telemetry') or {}).get(k,0) for g in games) for k in ERROR_KEYS}
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat(),
               all_done=all_done,errors=errors,new_sweeps=[r['team'] for r in sweeps],new_top50_sweeps=top50_sweeps,
               wins=sum(g['result']=='win' for g in games),draws=sum(g['result']=='draw' for g in games),
               losses=sum(g['result']=='loss' for g in games),lost_previously_won_seats=lost_wins,
               passed=bool(top50_sweeps) and not lost_wins and all_done and not any(errors.values()))
    save()
    print(json.dumps({k:v for k,v in out.items() if k!='games'}),flush=True)
