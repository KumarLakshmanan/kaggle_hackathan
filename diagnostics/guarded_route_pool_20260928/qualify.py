"""Original-framework parity and full frozen-target tests for a selected arm."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.guarded_route_pool_20260928.search import context, read, write, TARGETS, FULL, SOURCE_SHA, sha
from diagnostics.opening_probe_v2_20260928.qualify import play
from diagnostics.local_target_20260928.run_lock import exclusive_run


def key(row):
    return row['rival'], row['candidate_seat']


def main(phase, workers):
    pool = context()
    selected = read(HERE / 'selection.json')
    assert selected['complete'] and selected['passed'] and selected['source_sha256'] == SOURCE_SHA
    assert selected['pool_sha256'] == sha(HERE / 'pool.json') and selected['screen_sha256'] == sha(HERE / 'screen.json')
    assert sha(selected['candidate']) == selected['candidate_sha256'] == sha(selected['backup'])
    screen = read(HERE / 'screen.json')
    source = {(r['rival'], r['candidate_seat']): r for r in read(FULL)['games']}
    main_controls = {}
    manifest = read(TARGETS)
    for fixture in manifest['live_losses'] + manifest['current_top20']:
        for row in fixture['baseline_frozen_tape_both_seat_outcomes']:
            main_controls[(fixture['fixture_id'], row['seat'])] = row
    for row in screen['games']:
        row_key = (row['fixture_id'], row['candidate_seat'])
        if row['version'] == 'control-source':
            source[row_key] = row
        elif row['version'] == 'control-main':
            main_controls[row_key] = row
    versions = {choice['version'] for choice in selected['selected_groups']}
    fast = {(r['fixture_id'], r['candidate_seat']): r for r in screen['games'] if r['version'] in versions}
    groups = {choice['group'] for choice in selected['selected_groups']}
    fixtures = ([f for group in sorted(groups) for f in pool['fixtures'][group]] if phase == 'parity'
                else manifest['live_losses'] + manifest['current_top20'])
    assert len({f['fixture_id'] for f in fixtures}) == len(fixtures)
    jobs = []
    for fixture in fixtures:
        for seat in (0, 1):
            row_key = (fixture['fixture_id'], seat)
            prior, original = source[row_key], main_controls[row_key]
            jobs.append(dict(version='selected', rival=fixture['fixture_id'], team=fixture['team'],
                             panel='public-win' if fixture['fixture_id'].startswith('public-win-') else
                                   'loss30' if fixture['fixture_id'].startswith('live-') else 'top20',
                             seed=int(fixture['seed']), candidate_seat=seat, path=selected['candidate'],
                             candidate_sha256=selected['candidate_sha256'], opponent='rawroute:' + fixture['source_action_tape_path'],
                             opponent_action_sha256=fixture['source_opponent_action_sha256'], plan_sha256=pool['plan_sha256'],
                             selection_sha256=sha(HERE / 'selection.json'),
                             source_result=prior['result'], source_margin=prior['margin'],
                             original_result=original['result'], original_margin=original['margin']))
    expected = {key(job): job for job in jobs}
    assert len(expected) == len(jobs)
    checkpoint = HERE / ('native_' + phase + '.jsonl')
    if checkpoint.exists():
        rows = [json.loads(line) for line in checkpoint.read_text(encoding='utf-8').splitlines()]
    elif phase == 'full':
        parity = read(HERE / 'native_parity.json')
        assert parity['complete'] and parity['passed'] and parity['candidate_sha256'] == selected['candidate_sha256']
        assert parity['selection_sha256'] == sha(HERE / 'selection.json')
        rows = [r for r in parity['games'] if key(r) in expected]
        checkpoint.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    else:
        rows = []
    for row in rows:
        assert all(row[field] == value for field, value in expected[key(row)].items())
    done = {key(row) for row in rows}; assert len(done) == len(rows)
    pending = [job for job in jobs if key(job) not in done]
    print(f'Native {phase} {len(rows)}/{len(jobs)}', flush=True)
    with checkpoint.open('a', encoding='utf-8') as output:
        for start in range(0, len(pending), 16):
            with ProcessPoolExecutor(max_workers=workers) as executor:
                for future in as_completed([executor.submit(play, job) for job in pending[start:start+16]]):
                    row = future.result(); assert key(row) not in done
                    done.add(key(row)); rows.append(row)
                    output.write(json.dumps(row, ensure_ascii=False) + '\n'); output.flush()
                    if len(rows) % 2 == 0:
                        print(f'Native {phase} {len(rows)}/{len(jobs)} {row["team"]}: {row["result"]} {row["margin"]:+.0f}', flush=True)
    fields = ('candidate_reward', 'opponent_reward', 'candidate_telemetry', 'candidate_status', 'opponent_status', 'frames')
    mismatches = [dict(rival=r['rival'], seat=r['candidate_seat'], fields=[field for field in fields if r[field] != fast[key(r)][field]])
                  for r in rows if key(r) in fast and any(r[field] != fast[key(r)][field] for field in fields)]
    clean = all(r['frames'] == 720 and r['candidate_status'] == r['opponent_status'] == 'DONE'
                and not r['candidate_errors'] and not r['opponent_errors'] for r in rows)
    preserved = all(r['result'] == 'win' for r in rows if r['source_result'] == 'win' or r['original_result'] == 'win')
    summaries, rescued = [], []
    for panel in ('loss30', 'top20', 'public-win'):
        arm = [r for r in rows if r['panel'] == panel]
        if not arm:
            continue
        pairs = {r['rival']: [x for x in arm if x['rival'] == r['rival']] for r in arm}
        new = [rs[0]['team'] for rs in pairs.values() if all(r['result'] == 'win' for r in rs)
               and any(r['source_result'] != 'win' for r in rs)]
        if panel == 'top20':
            rescued.extend(new)
        summaries.append(dict(panel=panel, fixtures=len(pairs), both_seat_wins=sum(all(r['result'] == 'win' for r in rs) for rs in pairs.values()),
                              WDL=[sum(r['result'] == outcome for r in arm) for outcome in ('win', 'draw', 'loss')], rescued=new))
    result = dict(complete=len(rows) == len(jobs), passed=clean and preserved and not mismatches and bool(rescued),
                  candidate=selected['candidate'], candidate_sha256=selected['candidate_sha256'],
                  selection_sha256=sha(HERE / 'selection.json'), plan_sha256=pool['plan_sha256'],
                  clean=clean, all_prior_winning_seats_preserved=preserved, fast_native_mismatches=mismatches,
                  summaries=summaries, completed_at_utc=datetime.now(timezone.utc).isoformat(), games=sorted(rows, key=key))
    write(HERE / ('native_' + phase + '.json'), result)
    print(json.dumps({k: v for k, v in result.items() if k != 'games'}, indent=2, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=('parity', 'full'))
    parser.add_argument('--workers', type=int, default=2); args = parser.parse_args()
    with exclusive_run(HERE / 'qualify.lock'):
        main(args.phase, args.workers)
