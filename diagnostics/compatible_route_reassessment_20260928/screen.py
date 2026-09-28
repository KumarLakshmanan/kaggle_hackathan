from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.opening_probe_v2_20260928.qualify import play, sha, MANIFEST, MANIFEST_SHA, REFS

TARGETS = {'DECEM', 'Boey', 'Vadim Vasilenko'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('pilot', 'full'))
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    candidate = json.loads((HERE / 'candidate_manifest.json').read_text())
    assert sha(HERE / 'PLAN.md') == candidate['plan_sha256']
    assert sha(candidate['candidate']) == candidate['candidate_sha256']
    assert sha(ROOT / 'main.py') == candidate['source_sha256']
    assert sha(MANIFEST) == MANIFEST_SHA
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if args.phase == 'pilot':
        fixtures = [f for f in manifest['current_top20'] if f['team'] in TARGETS
                    or f['team'] == 'Yizhou' or f['team'].startswith('Kaggledew Valley')]
        assert len(fixtures) == 5
    else:
        pilot = json.loads((HERE / 'pilot.json').read_text(encoding='utf-8'))
        assert pilot['complete'] and pilot['passed'] and pilot['candidate_sha256'] == candidate['candidate_sha256']
        fixtures = manifest['live_losses'] + manifest['current_top20']
    jobs = []
    for fixture in fixtures:
        for seat in (0, 1):
            baseline = next(r for r in fixture['baseline_frozen_tape_both_seat_outcomes'] if r['seat'] == seat)
            jobs.append(dict(version='new', rival=fixture['fixture_id'], team=fixture['team'],
                seed=int(fixture['seed']), candidate_seat=seat, path=candidate['candidate'],
                candidate_sha256=candidate['candidate_sha256'],
                opponent='rawroute:' + fixture['source_action_tape_path'],
                opponent_action_sha256=fixture['source_opponent_action_sha256'],
                baseline_result=baseline['result'], baseline_margin=baseline['margin'],
                plan_sha256=candidate['plan_sha256']))
    checkpoint = HERE / (args.phase + '.jsonl')
    rows = [json.loads(line) for line in checkpoint.read_text(encoding='utf-8').splitlines()] if checkpoint.exists() else []
    expected = {(j['rival'], j['candidate_seat']): j for j in jobs}
    for row in rows:
        assert all(row[k] == v for k,v in expected[(row['rival'], row['candidate_seat'])].items())
    completed = {(r['rival'],r['candidate_seat']) for r in rows}
    assert len(completed) == len(rows)
    pending = [j for j in jobs if (j['rival'],j['candidate_seat']) not in completed]
    with checkpoint.open('a', encoding='utf-8') as output:
        for start in range(0, len(pending), 16):
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                for future in as_completed([pool.submit(play,j) for j in pending[start:start+16]]):
                    row = future.result()
                    rows.append(row)
                    output.write(json.dumps(row, ensure_ascii=False) + '\n')
                    output.flush()
                    print(f'{len(rows)}/{len(jobs)} {row["team"]} seat{row["candidate_seat"]} '
                          f'{row["result"]} {row["margin"]:+.0f} delta {row["margin"]-row["baseline_margin"]:+.0f}', flush=True)
    pairs = {r['rival']: [] for r in rows}
    for row in rows:
        pairs[row['rival']].append(row)
    all_done = all(r['frames'] == 720 and r['candidate_status'] == r['opponent_status'] == 'DONE' for r in rows)
    no_errors = all(not r['candidate_errors'] and not r['opponent_errors'] for r in rows)
    preserved = all(r['result'] == 'win' for r in rows if r['baseline_result'] == 'win')
    rescued = [pair[0]['team'] for pair in pairs.values() if any(r['baseline_result'] != 'win' for r in pair)
               and all(r['result'] == 'win' for r in pair)]
    passed = all_done and no_errors and preserved and bool(rescued)
    result = dict(complete=True, passed=passed, candidate_sha256=candidate['candidate_sha256'],
        plan_sha256=candidate['plan_sha256'], manifest_sha256=MANIFEST_SHA,
        phase=args.phase, all_done=all_done, no_errors=no_errors, incumbent_win_preservation=preserved,
        rescued_both_seat=rescued, games=sorted(rows,key=lambda r:(r['rival'],r['candidate_seat'])))
    (HERE / (args.phase+'.json')).write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    assert sha(ROOT / 'main.py') == candidate['source_sha256']
    print(json.dumps({k:v for k,v in result.items() if k != 'games'},indent=2))


if __name__ == '__main__':
    main()
