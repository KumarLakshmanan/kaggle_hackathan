from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from diagnostics.shunki_funded_purchase_20260927.panels import play, totals


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8', errors='replace')
    manifest = json.loads((HERE / 'build_manifest.json').read_text())
    gate = json.loads((HERE / 'pilot.json').read_text())
    assert gate['complete'] and gate['passed'] and gate['candidate_sha256'] == manifest['candidate_sha256']
    assert hashlib.sha256((HERE / 'PLAN.md').read_bytes()).hexdigest() == manifest['plan_sha256']
    target = HERE / 'panels.json'
    assert not target.exists()
    sources = {'current100': ROOT / 'diagnostics/current_top100_20260927_0730/routes/summary.json',
               'legacy50': ROOT / 'diagnostics/top50_refresh_20260927_2303/routes/summary.json'}
    entries = {k: json.loads(v.read_text(encoding='utf8')) for k,v in sources.items()}
    assert len(entries['current100']) == 100 and len(entries['legacy50']) == 50
    old_current = json.loads((ROOT / 'diagnostics/current_top100_20260927_0730/assessment.json').read_text())
    old_legacy = json.loads((ROOT / 'diagnostics/shunki_disjoint_integration_20260927/top50_reuse_proof.json').read_text())
    assert old_current['candidate_sha256'] == old_legacy['candidate_sha256'] == manifest['source_sha256']
    old = {('current100', g['team'], g['candidate_seat']): g['margin'] for g in old_current['games']}
    old.update({('legacy50', g['team'], g['seat']): g['margin'] for g in old_legacy['branches']})
    jobs = [(manifest['candidate'], manifest['candidate_sha256'], panel, entry, seat)
            for panel, rows in entries.items() for entry in rows for seat in (0,1)]
    out = dict(started_at_utc=datetime.now(timezone.utc).isoformat(), candidate_sha256=manifest['candidate_sha256'],
               plan_sha256=manifest['plan_sha256'], source_hashes={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in sources.items()},
               complete=False, games=[], reused_games=0, intended_games=300)
    def save():
        current = [g for g in out['games'] if g['panel'] == 'current100']
        legacy = [g for g in out['games'] if g['panel'] == 'legacy50']
        out['summary'] = {'current100': totals(current,100),
                          'current50': totals([g for g in current if g['rank'] <= 50],50),
                          'legacy50': totals(legacy,50)}
        out['all_done'] = all(g['candidate_status'] == g['opponent_status'] == 'DONE' and g['frames'] == 720 for g in out['games'])
        out['error_rows'] = [{'panel':g['panel'],'team':g['team'],'seat':g['candidate_seat'],'key':k,'value':v}
                             for g in out['games'] for k,v in (g.get('candidate_telemetry') or {}).items()
                             if isinstance(v,(int,float)) and v and ('error' in k.lower() or 'collision' in k.lower())]
        out['lost_winning_seats'] = [{'panel':g['panel'],'team':g['team'],'seat':g['candidate_seat'],
                                     'old_margin':old[g['panel'],g['team'],g['candidate_seat']],'new_margin':g['margin']}
                                    for g in out['games'] if old[g['panel'],g['team'],g['candidate_seat']] > 0 and g['margin'] <= 0]
        target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    save()
    cohorts = [('current50',[j for j in jobs if j[2]=='current100' and j[3]['rank'] <= 50],37),
               ('current100',[j for j in jobs if j[2]=='current100' and j[3]['rank'] > 50],78),
               ('legacy50',[j for j in jobs if j[2]=='legacy50'],44)]
    for label, cohort, required in cohorts:
        out['running_cohort'] = label
        save()
        with ProcessPoolExecutor(max_workers=4) as pool:
            for future in as_completed([pool.submit(play,j) for j in cohort]):
                g = future.result()
                out['games'].append(g)
                save()
                print(f"{len(out['games'])}/300 {g['panel']} {g['team']} seat={g['candidate_seat']} {g['result']} {g['margin']:+.0f}",flush=True)
        if (out['summary'][label]['sweeps'] < required or not out['all_done'] or out['error_rows'] or out['lost_winning_seats']):
            out.update(complete=len(out['games'])==300, terminated_early=len(out['games'])!=300,
                       passed=False, failed_completed_cohort=label, running_cohort=None,
                       completed_at_utc=datetime.now(timezone.utc).isoformat())
            save()
            print('REJECT '+json.dumps({k:out[k] for k in ('summary','all_done','error_rows','lost_winning_seats','failed_completed_cohort')}),flush=True)
            raise SystemExit(0)
    comparisons=[]
    for panel, rows in entries.items():
        for entry in rows:
            pair=sorted([g for g in out['games'] if g['panel']==panel and g['team_id']==entry['team_id']],key=lambda g:g['candidate_seat'])
            comparisons.append(dict(panel=panel,team=entry['team'],rank=entry.get('rank'),
                                    old_margins=[old[panel,entry['team'],seat] for seat in (0,1)],new_margins=[g['margin'] for g in pair]))
    out.update(complete=True,passed=True,running_cohort=None,comparisons=comparisons,
               completed_at_utc=datetime.now(timezone.utc).isoformat())
    save()
    print('PASS '+json.dumps(out['summary']),flush=True)
