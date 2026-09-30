"""Sequential twelve-game replay test for the frozen six-fixture integration."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from diagnostics.local_target_20260928.run_lock import exclusive_run
from diagnostics.stream_replay_io_20260928.fast_game_cached import play

EXPECTED_FIXTURES = {
    'live-114211346', 'live-114223338', 'public-win-114216671',
    'public-win-114217947', 'public-win-114248439', 'public-win-114258739',
}
EXPECTED_SEATS = (0, 1)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json_once(path, value):
    path = Path(path)
    data = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    if path.exists():
        old = json.loads(path.read_text(encoding='utf-8'))
        new = json.loads(data.decode('utf-8'))
        old.pop('completed_at_utc', None)
        new.pop('completed_at_utc', None)
        assert old == new, f'Existing output differs: {path}'
        return
    with path.open('xb') as stream:
        stream.write(data)


def verify_frozen():
    manifest = read(HERE / 'frozen_manifest.json')
    assert manifest['complete'] and manifest['diagnostic_only']
    for name, digest in manifest['bindings'].items():
        p = Path(name)
        assert p.exists() and sha(p) == digest, f'Frozen input changed: {p}'
    parent_manifest = read(HERE / 'goose4_parent_manifest.json')
    for name, digest in parent_manifest['bindings'].items():
        p = Path(name)
        assert p.exists() and sha(p) == digest, f'Parent Goose4 binding changed: {p}'
    preflight = read(HERE / 'preflight.json')
    assert preflight['passed'] and preflight['static_only'] and preflight['games_run'] == 0
    assert preflight['trigger_seats'] == 12 and preflight['reusable_parent_seats'] == 196
    assert preflight['reuse_audit']['normalized_activation_passed']
    assert sha(HERE / 'candidate.py') == manifest['candidate_sha256']
    assert sha(HERE / 'panel.json') == manifest['panel_sha256']
    panel = read(HERE / 'panel.json')
    assert {f['fixture_id'] for f in panel['fixtures']} == EXPECTED_FIXTURES
    assert len(panel['fixtures']) == 6 and panel['candidate_games'] == 12
    return manifest, panel


def source_baselines():
    target = read(ROOT / 'diagnostics/adaptive_donor_pair_repair_20260928/full_results.json')
    public = read(ROOT / 'diagnostics/a44_source_bridge_goose_4leaf_20260929/source_public.json')
    a44 = read(HERE / 'a44_controls.json')
    rows = {(r['fixture_id'], int(r['candidate_seat'])): r for r in a44['rows']}
    assert target['complete'] and target['clean'] and public['complete'] and public['clean']
    assert len(rows) == 208 and a44['candidate_sha256'] == read(HERE / 'preflight.json')['source_a44_sha256']
    return rows


def expected_by_key(panel):
    rows = {(r['fixture_id'], int(r['seat'])): r for r in panel['expected_seats']}
    assert len(rows) == 12
    return rows


def check_telemetry(row, expected):
    t = row.get('candidate_telemetry', {})
    key = expected['rule_key']
    pair = expected['shop_pair_key']
    route = str(expected['selected_route'])
    checks = {
        'clean': row['candidate_status'] == 'DONE' and row['opponent_status'] == 'DONE'
                 and row['frames'] == 720 and not row.get('candidate_errors'),
        'branch72': t.get('bridge_selected') == 'source'
                    and t.get('a44_goose4_branch72') == 'source'
                    and t.get('a44_smoothie_branch72') == 'source',
        'key72': t.get('a44_goose4_key72') == key and t.get('a44_smoothie_key72') == key,
        'goose4_nonoverlap': t.get('a44_goose4_route', '') == ''
                             and t.get('a44_goose4_turns', 0) == 0
                             and t.get('a44_goose4_errors', 0) == 0,
        'smoothie_route72': t.get('a44_smoothie_active72') is True
                            and t.get('a44_smoothie_route72') == '113470868',
        'pair144': t.get('a44_smoothie_pair144') == pair
                   and t.get('a44_smoothie_route144') == route,
        'turn_count': t.get('a44_smoothie_turns') == 575
                      and t.get('a44_smoothie_errors', 0) == 0,
    }
    return checks


def run_candidate():
    manifest, panel = verify_frozen()
    controls = source_baselines()
    expected_seats = expected_by_key(panel)
    fixture_order = panel['fixtures']
    expected_keys = {(f['fixture_id'], seat) for f in fixture_order for seat in EXPECTED_SEATS}
    assert expected_keys == set(expected_seats)
    ledger = HERE / 'candidate.jsonl'
    receipt = HERE / 'candidate.json'
    rows = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines() if line.strip()] if ledger.exists() else []
    done = {(r['fixture_id'], int(r['candidate_seat'])) for r in rows}
    assert len(rows) == len(done) and done <= expected_keys
    candidate_path = HERE / 'candidate.py'
    digest = manifest['candidate_sha256']
    with ledger.open('a', encoding='utf-8') as stream:
        for fixture in fixture_order:
            for seat in EXPECTED_SEATS:
                key = fixture['fixture_id'], seat
                if key in done:
                    continue
                row = play(fixture, candidate_path, digest, seat)
                row.update(version='a44_goose4_smoothie_source', panel=fixture['panel'],
                           panel_sha256=manifest['panel_sha256'], runner_sha256=sha(HERE / 'run_six.py'))
                base = controls[key]
                row.update(parent_result=base['result'], parent_margin=base['margin'],
                           delta_own=row['candidate_reward'] - base['candidate_reward'],
                           delta_rival=row['opponent_reward'] - base['opponent_reward'],
                           delta_margin=row['margin'] - base['margin'])
                checks = check_telemetry(row, expected_seats[key])
                row['activation_checks'] = checks
                row['activation_passed'] = all(checks.values())
                row['clean'] = checks['clean']
                rows.append(row)
                done.add(key)
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                stream.flush()
                print('six_fixture_candidate', len(rows), '/', len(expected_keys),
                      fixture['fixture_id'], seat, row['result'], row['margin'],
                      'activation', row['activation_passed'], flush=True)
    assert done == expected_keys
    out = dict(complete=True, clean=all(r['clean'] for r in rows),
               activation_passed=all(r['activation_passed'] for r in rows),
               diagnostic_only=True, fixed_tape_only=True, version='a44_goose4_smoothie_source',
               candidate_sha256=digest, source_a44_sha256=manifest['source_a44_sha256'],
               panel_sha256=manifest['panel_sha256'], runner_sha256=sha(HERE / 'run_six.py'),
               games=rows, completed_at_utc=datetime.now(timezone.utc).isoformat(), promotion=False)
    write_json_once(receipt, out)
    return out


def combined_report():
    manifest, panel = verify_frozen()
    new = read(HERE / 'candidate.json')
    reuse = read(HERE / 'reuse_rows.json')
    assert new['complete'] and new['clean'] and new['activation_passed']
    assert reuse['complete'] and reuse['normalized_activation_passed']
    new_rows = {(r['fixture_id'], int(r['candidate_seat'])): r for r in new['games']}
    reused = {(r['fixture_id'], int(r['candidate_seat'])): r for r in reuse['rows']}
    assert len(new_rows) == 12 and len(reused) == 196
    assert not (set(new_rows) & set(reused))
    combined = dict(reused)
    combined.update(new_rows)
    parent_panel = read(HERE / 'parent_panel.json')
    fixture_panel = {f['fixture_id']: f['panel'] for f in parent_panel['fixtures']}
    assert len(fixture_panel) == 104
    controls = source_baselines()
    summaries = {}
    for panel_name in ('loss30', 'top20', 'public-win'):
        ids = sorted(fid for fid, name in fixture_panel.items() if name == panel_name)
        crows = [combined[(fid, s)] for fid in ids for s in EXPECTED_SEATS]
        brows = [controls[(fid, s)] for fid in ids for s in EXPECTED_SEATS]
        wins = lambda rows: sum(r['result'] == 'win' for r in rows)
        sweeps = lambda rows: sum(all(combined[(fid, s)]['result'] == 'win' for s in EXPECTED_SEATS) for fid in ids)
        base_sweeps = sum(all(controls[(fid, s)]['result'] == 'win' for s in EXPECTED_SEATS) for fid in ids)
        regressions = sorted(fid for fid in ids if any(
            controls[(fid, s)]['result'] == 'win' and combined[(fid, s)]['result'] != 'win'
            for s in EXPECTED_SEATS))
        rescues = sorted(fid for fid in ids if all(combined[(fid, s)]['result'] == 'win' for s in EXPECTED_SEATS)
                         and not all(controls[(fid, s)]['result'] == 'win' for s in EXPECTED_SEATS))
        summaries[panel_name] = {'fixtures':len(ids),'games':len(crows),'candidate_wins':wins(crows),
            'a44_source_wins':wins(brows),'candidate_both_seat_sweeps':sweeps(crows),
            'a44_source_both_seat_sweeps':base_sweeps,'rescues':rescues,
            'source_winning_fixture_regressions':regressions}
    merged_rows=[]
    for key in sorted(combined):
        row=dict(combined[key])
        if key in reused:
            row['decision_equivalence_reuse'] = True
            row['reused_parent_candidate_sha256'] = reuse['parent_candidate_sha256']
        else:
            row['decision_equivalence_reuse'] = False
        merged_rows.append(row)
    out = {'complete':True,'diagnostic_only':True,'fixed_tape_only':True,
        'candidate_sha256':manifest['candidate_sha256'],'source_a44_sha256':manifest['source_a44_sha256'],
        'panel_sha256':manifest['full_panel_sha256'],'new_candidate_games':12,'equivalent_reused_parent_games':196,
        'summaries':summaries,'games':merged_rows,'completed_at_utc':datetime.now(timezone.utc).isoformat(),
        'promotion':False}
    write_json_once(HERE / 'combined_results.json', out)
    return {k:v for k,v in out.items() if k!='games'}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {'candidate', 'report'}:
        raise SystemExit('usage: run_six.py candidate|report')
    with exclusive_run(HERE / 'run.lock'):
        verify_frozen()
        if sys.argv[1] == 'candidate':
            print(json.dumps(run_candidate(), indent=2), flush=True)
        else:
            print(json.dumps(combined_report(), indent=2), flush=True)


if __name__ == '__main__':
    main()
