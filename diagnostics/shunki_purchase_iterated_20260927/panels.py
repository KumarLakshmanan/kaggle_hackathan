from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from diagnostics.shunki_funded_purchase_20260927.panels import play as replay_play, totals

def play(job):
    row = replay_play(job)
    row['self_control'] = bool(job[3].get('self_control', False))
    return row

if __name__ == '__main__':
    manifest = json.loads((HERE / 'build_manifest.json').read_text())
    gate = json.loads((HERE / 'pilot.json').read_text())
    assert gate['complete'] and gate['passed'] and gate['candidate_sha256'] == manifest['candidate_sha256']
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(HERE / 'PLAN.md') == manifest['plan_sha256']
    paths = {'current100': ROOT / 'diagnostics/current_top100_20260927_1137/routes/summary.json',
             'original50': ROOT / 'diagnostics/top50_refresh_20260927_2303/routes/summary.json'}
    entries = {k: json.loads(p.read_text(encoding='utf8')) for k,p in paths.items()}
    assert len(entries['current100']) == 100 and len(entries['original50']) == 50
    old_paths = {'current100': ROOT / 'diagnostics/current_top100_20260927_1137/assessment.json',
                 'original50': ROOT / 'diagnostics/shunki_disjoint_integration_20260927/top50_reuse_proof.json'}
    baselines = {k: json.loads(p.read_text(encoding='utf8')) for k,p in old_paths.items()}
    assert all(d['candidate_sha256'] == manifest['incumbent_sha256'] for d in baselines.values())
    old = {('current100', g['team'], g['candidate_seat']): g['margin'] for g in baselines['current100']['games']}
    old.update({('original50', g['team'], g['seat']): g['margin'] for g in baselines['original50']['branches']})
    jobs = [(manifest['candidate'], manifest['candidate_sha256'], panel, row, seat)
            for panel, rows in entries.items() for row in rows for seat in (0,1)]
    assert len(jobs) == 300
    target = HERE / 'panels.json'
    assert not target.exists()
    out = dict(started_at_utc=datetime.now(timezone.utc).isoformat(), candidate_sha256=manifest['candidate_sha256'],
               plan_sha256=manifest['plan_sha256'], script_sha256=sha(Path(__file__)),
               source_hashes={k: sha(p) for k,p in paths.items()}, baseline_hashes={k: sha(p) for k,p in old_paths.items()},
               route_file_hashes={str(row['path']): sha(Path(row['path'])) for rows in entries.values() for row in rows},
               intended_games=300, reused_candidate_games=0, complete=False, games=[])
    def save():
        current = [g for g in out['games'] if g['panel'] == 'current100' and not g['self_control']]
        original = [g for g in out['games'] if g['panel'] == 'original50']
        control = [g for g in out['games'] if g['self_control']]
        out['summary'] = {'current100_external': totals(current, 99),
                          'current50': totals([g for g in current if g['rank'] <= 50], 50),
                          'original50': totals(original, 50), 'self_control': totals(control, 1)}
        out['all_done'] = all(g['candidate_status'] == g['opponent_status'] == 'DONE' and g['frames'] == 720 for g in out['games'])
        out['error_rows'] = [{'panel': g['panel'], 'team': g['team'], 'seat': g['candidate_seat'], 'key': k, 'count': v}
                             for g in out['games'] for k,v in (g.get('candidate_telemetry') or {}).items()
                             if isinstance(v, (int,float)) and v and ('error' in k.lower() or 'collision' in k.lower())]
        out['lost_winning_seats'] = [{'panel':g['panel'], 'team':g['team'], 'seat':g['candidate_seat'],
                                     'old_margin':old[g['panel'],g['team'],g['candidate_seat']], 'new_margin':g['margin']}
                                    for g in out['games'] if old[g['panel'],g['team'],g['candidate_seat']] > 0 and g['margin'] <= 0]
        target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(play, job) for job in jobs]):
            out['games'].append(future.result())
            save()
            if len(out['games']) % 20 == 0:
                print(f'Panels: {len(out["games"])}/300 games complete', flush=True)
    s = out['summary']
    passed = (s['current100_external']['sweeps'] >= 73 and s['current50']['sweeps'] >= 36
              and s['original50']['sweeps'] >= 44 and not out['lost_winning_seats'] and not out['error_rows'] and out['all_done'])
    out['comparisons'] = [dict(panel=panel, team=row['team'], rank=row.get('rank'), self_control=bool(row.get('self_control')),
                               old_margins=[old[panel,row['team'],seat] for seat in (0,1)],
                               new_margins=[next(g['margin'] for g in out['games'] if g['panel'] == panel and g['team_id'] == row['team_id']
                                                 and g['candidate_seat'] == seat) for seat in (0,1)])
                          for panel, rows in entries.items() for row in rows]
    out.update(complete=True, passed=bool(passed), completed_at_utc=datetime.now(timezone.utc).isoformat())
    save()
    print('RESULT ' + json.dumps({k:out[k] for k in ('summary','all_done','error_rows','lost_winning_seats','passed')}), flush=True)
