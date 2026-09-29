"""Single-worker frozen diagnostic gate. No network calls."""
from datetime import datetime, timezone
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.physical_route_rollout_20260928.fast_game import play, sha
from diagnostics.local_target_20260928.run_lock import exclusive_run

SOURCE = ROOT / 'main_candidate_hire_recovery_integrated_20260928_367d2e76.py'
SOURCE_SHA = '367d2e7683472af526bdaee5af80c9e7fe59dfb2136475555a2970ef8beccaa0'
MANIFEST = ROOT / 'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
FULL = ROOT / 'diagnostics/observed_hire_recovery_20260928/native_full.json'
EPISODES = [114267880, 114289228, 114266440, 114265033, 114263239, 114254310]


def main():
    assert sha(SOURCE) == SOURCE_SHA
    assert sha(MANIFEST) == '524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
    assert sha(FULL) == '1cd02ac25079a1df229ad528c51a94ec467181a4adcd1e6ab13248ff4fd82545'
    out = HERE / 'screen.json'; assert not out.exists()
    provenance = HERE / 'candidate.json'
    candidate = HERE / 'candidate.py'
    if not provenance.exists():
        assert not candidate.exists()
        candidate.write_bytes(SOURCE.read_bytes() + b'\n\n' + (HERE / 'layer.py').read_bytes())
        compile(candidate.read_text(), str(candidate), 'exec')
        data = dict(source=str(SOURCE), source_sha256=SOURCE_SHA, candidate=str(candidate), candidate_sha256=sha(candidate),
                    plan_sha256=sha(HERE / 'PLAN.md'), layer_sha256=sha(HERE / 'layer.py'), helper_sha256=sha(__file__),
                    manifest_sha256=sha(MANIFEST), full_sha256=sha(FULL), frozen_at_utc=datetime.now(timezone.utc).isoformat())
        provenance.write_text(json.dumps(data, indent=2))
    data = json.loads(provenance.read_text())
    assert sha(candidate) == data['candidate_sha256'] and sha(HERE / 'PLAN.md') == data['plan_sha256']
    assert sha(__file__) == data['helper_sha256'] and sha(HERE / 'layer.py') == data['layer_sha256']
    m = json.loads(MANIFEST.read_text()); fixtures = m['live_losses'] + m['current_top20']
    selected = [next(f for f in fixtures if f['episode_id'] == episode) for episode in EPISODES]
    baseline = {(r['rival'], r['candidate_seat']): r for r in json.loads(FULL.read_text())['games'] if r['version'] == 'integrated'}
    ledger = HERE / 'screen.jsonl'
    rows = [json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
    done = {(r['fixture_id'], r['candidate_seat']) for r in rows}
    assert len(done) == len(rows) and all(r['candidate_sha256'] == data['candidate_sha256'] for r in rows)
    with ledger.open('a', encoding='utf-8') as output:
        for f in selected:
            for seat in (0, 1):
                if (f['fixture_id'], seat) in done:
                    continue
                row = play(f, candidate, data['candidate_sha256'], seat, HERE / (f['fixture_id'] + '_seat' + str(seat) + '.jsonl.gz'))
                parent = baseline[(f['fixture_id'], seat)]
                row.update(team=f['team'], parent_result=parent['result'], parent_margin=parent['margin'],
                           delta_own=row['candidate_reward']-parent['candidate_reward'],
                           delta_rival=row['opponent_reward']-parent['opponent_reward'],
                           delta_margin=row['margin']-parent['margin'])
                rows.append(row); output.write(json.dumps(row) + '\n'); output.flush()
                print(len(rows), '/12', f['team'], seat, row['result'], row['margin'], 'delivery starts', row['candidate_telemetry'].get('seed_delivery_starts'), flush=True)
    clean = all(r['frames'] == 720 and r['candidate_status'] == r['opponent_status'] == 'DONE' and not r['candidate_errors'] for r in rows)
    regressions = [r['fixture_id'] + ':' + str(r['candidate_seat']) for r in rows if r['parent_result'] == 'win' and r['result'] != 'win']
    rescued = all(r['result'] == 'win' for r in rows if r['team'] == 'DECEM')
    result = dict(complete=len(rows) == 12, passed=clean and not regressions and rescued, clean=clean,
                  regressions=regressions, decem_rescued=rescued, diagnostic_only=True, games=rows, **data,
                  completed_at_utc=datetime.now(timezone.utc).isoformat())
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('Development gate', result['passed'], flush=True)


if __name__ == '__main__':
    with exclusive_run(HERE / 'screen.lock'):
        main()
