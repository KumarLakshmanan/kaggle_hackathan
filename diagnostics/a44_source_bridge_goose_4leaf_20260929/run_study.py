"""Single-worker fixed-tape outcomes for the frozen four-leaf a44 candidate."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from diagnostics.local_target_20260928.run_lock import exclusive_run
from diagnostics.stream_replay_io_20260928.fast_game_cached import play


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def resolved(path):
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def verify_frozen():
    manifest = read(HERE / 'frozen_manifest.json')
    for name, digest in manifest['bindings'].items():
        p = resolved(name)
        assert p.exists() and sha(p) == digest, f'Frozen input changed: {p}'
    preflight = read(HERE / 'preflight.json')
    assert preflight['passed'] and preflight['candidate_sha256'] == manifest['candidate_sha256']
    assert sha(HERE / 'candidate.py') == manifest['candidate_sha256']
    return manifest


def write_once(path, value):
    path = Path(path)
    data = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    if path.exists():
        previous = json.loads(path.read_text(encoding='utf-8'))
        current = json.loads(data.decode('utf-8'))
        previous.pop('completed_at_utc', None)
        current.pop('completed_at_utc', None)
        assert previous == current, f'Existing output differs: {path}'
        return
    with path.open('xb') as stream:
        stream.write(data)


def panel_data():
    panel = read(HERE / 'panel.json')
    features = {(r['fixture_id'], r['seat']): r for r in read(HERE / 'feature_rows.json')['rows']}
    return panel, features


def source_public_controls():
    verify_frozen()
    panel, _ = panel_data()
    fixtures = [f for f in panel['fixtures'] if f['panel'] == 'public-win']
    expected = {(f['fixture_id'], seat) for f in fixtures for seat in (0, 1)}
    ledger = HERE / 'source_public.jsonl'
    receipt = HERE / 'source_public.json'
    rows = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()] if ledger.exists() else []
    done = {(r['fixture_id'], r['candidate_seat']) for r in rows}
    assert len(rows) == len(done) and done <= expected
    source_path = HERE / 'source_a44.py'
    source_sha = read(HERE / 'frozen_manifest.json')['source_a44_sha256']
    with ledger.open('a', encoding='utf-8') as stream:
        for fixture in fixtures:
            for seat in (0, 1):
                key = fixture['fixture_id'], seat
                if key in done:
                    continue
                row = play(fixture, source_path, source_sha, seat)
                row.update(version='a44_source_public', panel='public-win',
                           pool_sha256=read(HERE / 'frozen_manifest.json')['panel_sha256'],
                           helper_sha256=sha(HERE / 'run_study.py'))
                row['clean'] = (row['frames'] == 720 and row['candidate_status'] == 'DONE'
                                and row['opponent_status'] == 'DONE' and not row['candidate_errors'])
                rows.append(row)
                done.add(key)
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                stream.flush()
                print('source_public', len(rows), '/', len(expected), fixture['fixture_id'], seat,
                      row['result'], row['margin'], flush=True)
    assert done == expected
    out = dict(complete=True, clean=all(r['clean'] for r in rows), version='a44_source_public',
               candidate_sha256=source_sha, panel_sha256=read(HERE / 'frozen_manifest.json')['panel_sha256'],
               helper_sha256=sha(HERE / 'run_study.py'), games=rows,
               completed_at_utc=datetime.now(timezone.utc).isoformat(), fixed_tape_only=True)
    write_once(receipt, out)
    return out


def target_baselines(panel):
    return {(r['fixture_id'], r['candidate_seat']): r for r in panel['target_baseline_games']}


def run_candidate():
    manifest = verify_frozen()
    panel, features = panel_data()
    target_controls = target_baselines(panel)
    public_receipt = read(HERE / 'source_public.json')
    assert public_receipt['complete'] and public_receipt['clean']
    public_controls = {(r['fixture_id'], r['candidate_seat']): r for r in public_receipt['games']}
    controls = dict(target_controls)
    controls.update(public_controls)
    fixtures = panel['fixtures']
    expected = {(f['fixture_id'], seat) for f in fixtures for seat in (0, 1)}
    ledger = HERE / 'candidate.jsonl'
    receipt = HERE / 'candidate.json'
    rows = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()] if ledger.exists() else []
    done = {(r['fixture_id'], r['candidate_seat']) for r in rows}
    assert len(rows) == len(done) and done <= expected
    path = HERE / 'candidate.py'
    digest = manifest['candidate_sha256']
    with ledger.open('a', encoding='utf-8') as stream:
        for fixture in fixtures:
            for seat in (0, 1):
                key = fixture['fixture_id'], seat
                if key in done:
                    continue
                row = play(fixture, path, digest, seat)
                row.update(version='a44_goose4', panel=fixture['panel'],
                           pool_sha256=manifest['panel_sha256'], helper_sha256=sha(HERE / 'run_study.py'))
                row['clean'] = (row['frames'] == 720 and row['candidate_status'] == 'DONE'
                                and row['opponent_status'] == 'DONE' and not row['candidate_errors'])
                old = controls[key]
                row.update(parent_result=old['result'], parent_margin=old['margin'],
                           delta_own=row['candidate_reward'] - old['candidate_reward'],
                           delta_rival=row['opponent_reward'] - old['opponent_reward'],
                           delta_margin=row['margin'] - old['margin'])
                feature = features[key]
                expected_route = feature['selected_route'] or ''
                telem = row['candidate_telemetry']
                row['activation_passed'] = all((
                    telem.get('a44_goose4_branch72', '') == (feature['bridge_branch'] if feature['bridge_branch'] == 'source' else ''),
                    telem.get('a44_goose4_key72', '') == (feature['rule_key'] if feature['bridge_branch'] == 'source' else ''),
                    telem.get('a44_goose4_route', '') == expected_route,
                    telem.get('a44_goose4_turns', 0) == (647 if expected_route else 0),
                    telem.get('a44_goose4_errors', 0) == 0,
                ))
                rows.append(row)
                done.add(key)
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                stream.flush()
                print('candidate', len(rows), '/', len(expected), fixture['fixture_id'], seat,
                      row['result'], row['margin'], 'activation', row['activation_passed'], flush=True)
    assert done == expected
    out = dict(complete=True, clean=all(r['clean'] for r in rows),
               activation_passed=all(r['activation_passed'] for r in rows), version='a44_goose4',
               candidate_sha256=digest, source_a44_sha256=manifest['source_a44_sha256'],
               panel_sha256=manifest['panel_sha256'], helper_sha256=sha(HERE / 'run_study.py'),
               games=rows, completed_at_utc=datetime.now(timezone.utc).isoformat(), fixed_tape_only=True)
    write_once(receipt, out)
    return out


def report():
    manifest = verify_frozen()
    source_public = read(HERE / 'source_public.json')
    candidate = read(HERE / 'candidate.json')
    assert source_public['complete'] and candidate['complete']
    assert source_public['clean'] and candidate['clean'] and candidate['activation_passed']
    panel, _ = panel_data()
    parent = target_baselines(panel)
    parent.update({(r['fixture_id'], r['candidate_seat']): r for r in source_public['games']})
    games = {(r['fixture_id'], r['candidate_seat']): r for r in candidate['games']}
    assert len(games) == 208
    summaries = {}
    for panel_name in ('loss30', 'top20', 'public-win'):
        fixture_ids = [f['fixture_id'] for f in panel['fixtures'] if f['panel'] == panel_name]
        panel_rows = [games[(fid, seat)] for fid in fixture_ids for seat in (0, 1)]
        base_rows = [parent[(fid, seat)] for fid in fixture_ids for seat in (0, 1)]
        base_sweeps = sum(all(parent[(fid, s)]['result'] == 'win' for s in (0, 1)) for fid in fixture_ids)
        new_sweeps = sum(all(games[(fid, s)]['result'] == 'win' for s in (0, 1)) for fid in fixture_ids)
        regressions = sorted({fid for fid in fixture_ids for s in (0, 1)
                              if parent[(fid, s)]['result'] == 'win' and games[(fid, s)]['result'] != 'win'})
        rescues = sorted({fid for fid in fixture_ids
                          if all(games[(fid, s)]['result'] == 'win' for s in (0, 1))
                          and not all(parent[(fid, s)]['result'] == 'win' for s in (0, 1))})
        summaries[panel_name] = dict(fixtures=len(fixture_ids), games=len(panel_rows),
            candidate_WDL={x: sum(r['result'] == x for r in panel_rows) for x in ('win', 'draw', 'loss')},
            source_WDL={x: sum(r['result'] == x for r in base_rows) for x in ('win', 'draw', 'loss')},
            candidate_both_seat_sweeps=new_sweeps, source_both_seat_sweeps=base_sweeps,
            new_sweeps=rescues, source_winning_fixture_regressions=regressions,
            mean_delta_margin=sum(games[(fid, s)]['delta_margin'] for fid in fixture_ids for s in (0, 1)) / max(1, 2*len(fixture_ids)))
    combined_regressions = sorted({fid for fid in parent if parent[fid]['result'] == 'win'
                                   and games[fid]['result'] != 'win'})
    result = dict(complete=True, diagnostic_only=True, fixed_tape_only=True,
        candidate_sha256=manifest['candidate_sha256'], source_a44_sha256=manifest['source_a44_sha256'],
        panel_sha256=manifest['panel_sha256'], source_public_sha256=sha(HERE / 'source_public.json'),
        candidate_receipt_sha256=sha(HERE / 'candidate.json'), summaries=summaries,
        source_winning_seat_regressions=combined_regressions,
        completed_at_utc=datetime.now(timezone.utc).isoformat(), promotion=False)
    write_once(HERE / 'outcomes.json', result)
    return result


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {'controls', 'candidate', 'full', 'report'}:
        raise SystemExit('usage: run_study.py controls|candidate|full|report')
    with exclusive_run(HERE / 'run.lock'):
        verify_frozen()
        phase = sys.argv[1]
        if phase in ('controls', 'full'):
            source_public_controls()
        if phase in ('candidate', 'full'):
            run_candidate()
        if phase in ('report', 'full'):
            print(json.dumps(report(), indent=2), flush=True)


if __name__ == '__main__':
    main()
