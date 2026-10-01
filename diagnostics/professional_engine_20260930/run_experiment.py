"""Frozen paired qualification. Saved tapes are controls, native games decide strength."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; sys.path.insert(0, str(ROOT))
from diagnostics.local_target_20260928.run_lock import exclusive_run
from diagnostics.executable_engine_20260930.run_experiment import execute


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path, value): Path(path).write_text(json.dumps(value, indent=2), encoding='utf-8')
def points(row): return {'win':1., 'draw':.5, 'loss':0.}.get(row.get('result'), 0.)
def clean(row):
    return not row.get('error') and not row.get('candidate_errors') and not row.get('opponent_errors') and row.get('frames') == 720 and row.get('candidate_status') == row.get('opponent_status') == 'DONE'


def assess(rows):
    versions = sorted({r['version'] for r in rows}); groups = {}
    for v in versions:
        selected = [r for r in rows if r['version'] == v]
        groups[v] = {'games': len(selected), 'wins': sum(r.get('result') == 'win' for r in selected),
            'draws': sum(r.get('result') == 'draw' for r in selected), 'losses': sum(r.get('result') == 'loss' for r in selected),
            'points': sum(points(r) for r in selected), 'mean_margin': sum(r.get('margin', 0) for r in selected)/len(selected),
            'clean': all(clean(r) for r in selected), 'market_changes': sum(r.get('candidate_telemetry', {}).get('pro_market_changes', 0) for r in selected),
            'macro_activations': sum(r.get('candidate_telemetry', {}).get('pro_macro_activations', 0) for r in selected),
            'physical_turns': sum(r.get('candidate_telemetry', {}).get('pro_physical_turns', 0) for r in selected),
            'max_call_seconds': max([r.get('max_candidate_call_seconds', r.get('candidate_timing', {}).get('max_ms', 0)/1000) for r in selected])}
    decisions = {}
    base = groups['baseline']
    for v in versions:
        if v == 'baseline': continue
        per = {rival: sum(points(r) for r in rows if r['rival'] == rival and r['version'] == v)-sum(points(r) for r in rows if r['rival'] == rival and r['version'] == 'baseline') for rival in sorted({r['rival'] for r in rows})}
        activated = {r['seed'] for r in rows if r['version'] == v and r.get('candidate_telemetry', {}).get('pro_market_changes', 0)+r.get('candidate_telemetry', {}).get('pro_macro_activations', 0) > 0}
        gain = groups[v]['points']-base['points']
        decisions[v] = {'point_gain': gain, 'per_reference_gain': per, 'activated_seeds': len(activated),
            'screen_passed': groups[v]['clean'] and base['clean'] and gain > 0 and all(p >= 0 for p in per.values()) and len(activated) >= 2,
            'replay_passed': groups[v]['clean'] and base['clean'] and gain >= 0}
    passing = [v for v in decisions if decisions[v]['screen_passed']]
    survivor = max(passing, key=lambda v: (groups[v]['points'], groups[v]['mean_margin'])) if passing else None
    return {'groups': groups, 'decisions': decisions, 'screen_survivor': survivor}


def build_jobs(phase, candidate):
    versions = {'baseline': HERE/'baseline_main_bbffbe65.py'}
    if phase == 'screen': versions.update(full=HERE/'candidate_full.py', market=HERE/'candidate_market.py')
    else: versions['candidate'] = Path(candidate)
    refs = {'bbff': HERE/'baseline_main_bbffbe65.py', 'cb76': ROOT/'main_candidate_minimal_repair_20260929_cb76fbc4.py',
            'v35': ROOT/'diagnostics/public_ahmed_v35_20260927/public_v35_main.py',
            'c95': ROOT/'diagnostics/public_rayk_top_meta/public_c95_main.py'}
    jobs = []
    if phase in ('top20', 'top100'):
        source = json.loads((ROOT/'diagnostics/fresh90_improvement_20260929/combined_v2_top100_jobs.json').read_text())
        for fixture in source:
            if fixture['rank'] > (20 if phase == 'top20' else 100): continue
            for version, path in versions.items():
                jobs.append(dict(fixture, job_id=f'{version}:{fixture["fixture_id"]}:{fixture["candidate_seat"]}', kind='replay',
                    version=version, rival=fixture['team'], path=str(path), candidate_sha256=sha(path)))
    else:
        seeds = range(34000001, 34000005) if phase == 'screen' else range(34000101, 34000117)
        for seed in seeds:
            for rival, opponent in refs.items():
                for seat in (0, 1):
                    for version, path in versions.items():
                        jobs.append(dict(job_id=f'{version}:{seed}:{rival}:{seat}', kind='reactive' if phase == 'screen' else 'native',
                            version=version, rival=rival, seed=seed, candidate_seat=seat, path=str(path), candidate_sha256=sha(path),
                            opponent=str(opponent), opponent_sha256=sha(opponent)))
    return jobs


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=('screen', 'top20', 'top100', 'confirm'))
    parser.add_argument('--candidate', type=Path); parser.add_argument('--workers', type=int, default=4); args = parser.parse_args()
    assert 1 <= args.workers <= 6
    if args.phase != 'screen':
        assert args.candidate
        screen = json.loads((HERE/'screen_receipt.json').read_text())
        survivor = screen['assessment']['screen_survivor']; assert survivor is not None
        assert sha(args.candidate) == screen['candidate_hashes'][survivor]
    if args.phase == 'confirm':
        for phase in ('top20', 'top100'):
            receipt = json.loads((HERE/f'{phase}_receipt.json').read_text()); assert receipt['complete']
            assert receipt['assessment']['decisions']['candidate']['replay_passed']
        loader = json.loads((HERE/'loader_receipt.json').read_text()); assert loader['passed'] and loader['candidate_sha256'] == sha(args.candidate)
    paths = [HERE/'candidate_full.py', HERE/'candidate_market.py'] if args.phase == 'screen' else [args.candidate]
    for path in paths:
        manifest = json.loads(Path(path).with_suffix('.manifest.json').read_text()); assert manifest['candidate_sha256'] == sha(path)
        for source, digest in manifest['source_hashes'].items(): assert sha(source) == digest
        assert manifest['model_sha256'] == sha(HERE/'value_model.json')
    assert sha(HERE/'baseline_main_bbffbe65.py') == 'bbffbe65dee6e0dc4dd0147fec897df74e16760b76ec7d2a2b38f636bc90555f'
    jobs = build_jobs(args.phase, args.candidate); freeze = HERE/f'{args.phase}_jobs.json'
    if freeze.exists(): assert json.loads(freeze.read_text()) == jobs
    else: write(freeze, jobs)
    ledger = HERE/f'{args.phase}_results.jsonl'; receipt_path = HERE/f'{args.phase}_receipt.json'
    source_hashes = {str(p): sha(p) for p in [Path(__file__), ROOT/'diagnostics/executable_engine_20260930/run_experiment.py',
        ROOT/'diagnostics/physical_route_rollout_20260928/fast_reactive.py', ROOT/'diagnostics/opening_probe_v2_20260928/qualify.py']}
    with exclusive_run(ROOT/'diagnostics/.shared_game_run.lock'):
        previous = [json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
        lookup = {j['job_id']:j for j in jobs}; done = {r['job_id'] for r in previous}; assert len(done) == len(previous)
        for row in previous: assert row['candidate_sha256'] == lookup[row['job_id']]['candidate_sha256']
        if receipt_path.exists(): assert json.loads(receipt_path.read_text())['source_hashes'] == source_hashes
        if args.phase == 'top100' and not ledger.exists():
            for line in (HERE/'top20_results.jsonl').read_text().splitlines():
                row = json.loads(line); assert row['candidate_sha256'] == lookup[row['job_id']]['candidate_sha256']
                previous.append(row); done.add(row['job_id'])
            ledger.write_text(''.join(json.dumps(r)+'\n' for r in previous), encoding='utf-8')
        hashes = {v: sha(next(j['path'] for j in jobs if j['version'] == v)) for v in {j['version'] for j in jobs}}
        receipt = {'complete': False, 'started_at_utc': datetime.now(timezone.utc).isoformat(), 'source_hashes': source_hashes,
            'candidate_hashes': hashes, 'planned_games': len(jobs), 'jobs_sha256': sha(freeze)}
        write(receipt_path, receipt); rows = list(previous)
        with ledger.open('a', encoding='utf-8') as stream:
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                pending = {pool.submit(execute, j): j for j in jobs if j['job_id'] not in done}
                for future in as_completed(pending):
                    row = future.result(); rows.append(row); stream.write(json.dumps(row)+'\n'); stream.flush()
                    print(f'{len(rows)}/{len(jobs)} {row["job_id"]} {row.get("result", row.get("error_type"))} pro={row.get("candidate_telemetry", {}).get("pro_market_changes", 0)} physical={row.get("candidate_telemetry", {}).get("pro_physical_turns", 0)}', flush=True)
        receipt.update(complete=len(rows) == len(jobs), completed_at_utc=datetime.now(timezone.utc).isoformat(),
            results_sha256=sha(ledger), assessment=assess(rows))
        write(receipt_path, receipt); print(json.dumps(receipt['assessment'], indent=2), flush=True)


if __name__ == '__main__': main()
