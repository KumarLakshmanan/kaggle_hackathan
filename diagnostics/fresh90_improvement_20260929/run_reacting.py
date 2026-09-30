"""Frozen paired reacting games; exact cb76 baseline, all seats kept together."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import random
import sys

from run_panel import ROOT, HERE, sha
sys.path.insert(0, str(ROOT))
from diagnostics.local_target_20260928.run_lock import exclusive_run


def execute(job):
    try:
        if job['method'] == 'native':
            from diagnostics.opening_probe_v2_20260928.qualify import play
        else:
            from diagnostics.physical_route_rollout_20260928.fast_reactive import play
        return play(job)
    except Exception as error:
        return dict(job, error_type=type(error).__name__, error=str(error))


def assess(rows):
    if any(r.get('error') for r in rows):
        return {'passed': False, 'errors': [r for r in rows if r.get('error')]}
    def points(r):
        return {'win': 1.0, 'draw': .5, 'loss': 0}[r['result']]
    def block(selected):
        return dict(games=len(selected), points=sum(points(r) for r in selected),
                    wins=sum(r['result'] == 'win' for r in selected),
                    draws=sum(r['result'] == 'draw' for r in selected),
                    losses=sum(r['result'] == 'loss' for r in selected),
                    mean_margin=sum(r['margin'] for r in selected) / len(selected))
    opponents = {}
    for rival in sorted({r['rival'] for r in rows}):
        opponents[rival] = {v: block([r for r in rows if r['rival'] == rival and r['version'] == v])
                            for v in ('candidate', 'baseline')}
        opponents[rival]['delta'] = opponents[rival]['candidate']['points'] - opponents[rival]['baseline']['points']
    seeds = sorted({r['seed'] for r in rows})
    deltas = []
    seed_rows = []
    per_seed_scenarios = len(opponents) * 2
    for seed in seeds:
        totals = {v: sum(points(r) for r in rows if r['seed'] == seed and r['version'] == v)
                  for v in ('candidate', 'baseline')}
        delta = totals['candidate'] - totals['baseline']
        seed_rows.append(dict(seed=seed, **totals, delta=delta))
        deltas.append(delta)
    rng = random.Random(22929000)
    boots = sorted(sum(rng.choice(deltas) for _ in deltas) / (len(seeds) * per_seed_scenarios) for _ in range(10000))
    ci = [boots[249], boots[9749]]
    clean = all(not r.get('candidate_errors') and not r.get('opponent_errors') and
                r['frames'] == 720 and r['candidate_status'] == r['opponent_status'] == 'DONE' for r in rows)
    checks = dict(all_clean=clean, positive_points=sum(deltas) > 0,
                  no_per_opponent_regression=all(v['delta'] >= 0 for v in opponents.values()))
    return dict(all={v: block([r for r in rows if r['version'] == v]) for v in ('candidate', 'baseline')},
                per_opponent=opponents, seed_deltas=seed_rows,
                paired_point_rate_delta=sum(deltas) / (len(seeds) * per_seed_scenarios),
                bootstrap_95pct_whole_seed=ci, common_checks=checks,
                screen_passed=all(checks.values()) and sum(d >= 0 for d in deltas) >= .75 * len(deltas),
                confirmation_passed=all(checks.values()) and ci[0] > 0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('candidate', type=Path)
    parser.add_argument('label')
    parser.add_argument('phase', choices=('screen', 'confirm'))
    parser.add_argument('--pilot-seeds', type=int, default=0)
    args = parser.parse_args()
    assert args.pilot_seeds in (0, 2) and (not args.pilot_seeds or args.phase == 'screen')
    opponents = {
        'cb76': HERE / 'baseline_cb76fbc4.py',
        'ae349': ROOT / 'diagnostics/submission_top100_compare_20260929_1104/downloaded/main_ae349d83.py',
        'v35': ROOT / 'diagnostics/public_ahmed_v35_20260927/public_v35_main.py',
        'c95': ROOT / 'diagnostics/public_rayk_top_meta/public_c95_main.py',
    }
    versions = {'candidate': args.candidate.resolve(), 'baseline': HERE / 'baseline_cb76fbc4.py'}
    seeds = list(range(22929001, 22929009)) if args.phase == 'screen' else list(range(22929101, 22929133))
    if args.pilot_seeds:
        seeds = seeds[:args.pilot_seeds]
    if args.phase == 'confirm':
        screen = json.loads((HERE / f'{args.label}_screen_receipt.json').read_text())
        assert screen['candidate_sha256'] == sha(args.candidate) and screen['assessment']['screen_passed']
        operational = json.loads((HERE / f'{args.label}_operational_receipt.json').read_text())
        assert operational['candidate_sha256'] == sha(args.candidate) and operational['passed']
    jobs = []
    for seed in seeds:
        for rival, opponent in opponents.items():
            for seat in (0, 1):
                for version, path in versions.items():
                    jobs.append(dict(job_id=f'{seed}:{rival}:{seat}:{version}', version=version,
                                     rival=rival, seed=seed, candidate_seat=seat,
                                     path=str(path), candidate_sha256=sha(path), opponent=str(opponent),
                                     opponent_sha256=sha(opponent),
                                     method='native' if args.phase == 'confirm' else 'fast_native_transitions',
                                     configuration_seed_visible=None, fixed_tape=False, original_shop_seeded_episode=True))
    prefix = HERE / f'{args.label}_{args.phase}'
    freeze = prefix.with_name(prefix.name + '_jobs.json')
    ledger = prefix.with_name(prefix.name + '_results.jsonl')
    receipt_path = prefix.with_name(prefix.name + '_receipt.json')
    if freeze.exists():
        assert json.loads(freeze.read_text()) == jobs
    else:
        freeze.write_text(json.dumps(jobs, indent=2), encoding='utf-8')
    with exclusive_run(ROOT / 'diagnostics/.shared_game_run.lock'):
        rows = [json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
        done = {r['job_id'] for r in rows}
        assert len(rows) == len(done)
        lookup = {j['job_id']: j for j in jobs}
        for row in rows:
            assert all(row[k] == lookup[row['job_id']][k] for k in ('candidate_sha256', 'opponent_sha256', 'method'))
        with ledger.open('a', encoding='utf-8', newline='\n') as stream:
            with ProcessPoolExecutor(max_workers=6) as pool:
                pending = {pool.submit(execute, j): j for j in jobs if j['job_id'] not in done}
                for future in as_completed(pending):
                    row = future.result()
                    rows.append(row)
                    stream.write(json.dumps(row, ensure_ascii=True) + '\n')
                    stream.flush()
                    if len(rows) % 8 == 0:
                        print(f"{len(rows)}/{len(jobs)} {row['job_id']} {row.get('result', row.get('error_type'))}", flush=True)
        assert len(rows) == len(jobs)
        assessment = assess(rows)
        receipt = dict(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat(),
                       candidate_sha256=sha(args.candidate), jobs_sha256=sha(freeze), results_sha256=sha(ledger),
                       runner_sha256=sha(__file__), phase=args.phase, games=len(rows), assessment=assessment)
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        print(json.dumps(assessment, indent=2), flush=True)


if __name__ == '__main__':
    main()
