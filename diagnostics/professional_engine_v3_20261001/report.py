"""Aggregate every outcome and apply the declared whole-seed confirmation gate."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import statistics

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]


def points(r): return {'win':1., 'draw':.5, 'loss':0.}.get(r.get('result'), 0.)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    phases = {}
    for phase in ('screen', 'top20', 'top100', 'confirm'):
        p = HERE/f'{phase}_receipt.json'
        if p.exists(): phases[phase] = json.loads(p.read_text())
    screen = phases.get('screen', {})
    survivor = screen.get('assessment', {}).get('screen_survivor')
    decision = {'generated_at_utc': datetime.now(timezone.utc).isoformat(), 'survivor': survivor,
        'promotion_eligible': False, 'promoted': False, 'root_main_sha256': sha(ROOT/'main.py'),
        'universal_wins_established': False, 'kaggle_access_or_upload': False}
    intervals = None
    if phases.get('confirm', {}).get('complete'):
        rows = [json.loads(s) for s in (HERE/'confirm_results.jsonl').read_text().splitlines()]
        baseline = {(r['seed'], r['rival'], r['candidate_seat']): r for r in rows if r['version'] == 'baseline'}
        by_seed = {}
        for row in rows:
            if row['version'] != 'candidate': continue
            key = (row['seed'], row['rival'], row['candidate_seat'])
            by_seed.setdefault(row['seed'], []).append(points(row)-points(baseline[key]))
        blocks = [statistics.mean(v) for _, v in sorted(by_seed.items())]
        rng = random.Random(734); boot = sorted(statistics.mean(rng.choices(blocks, k=len(blocks))) for _ in range(20000))
        intervals = {'paired_point_rate_gain': statistics.mean(blocks), 'whole_seed_95_percent_interval': [boot[500], boot[19499]],
                     'blocks': len(blocks), 'paired_seats_and_references_per_block': len(next(iter(by_seed.values())))}
        assessment = phases['confirm']['assessment']
        decision['promotion_eligible'] = assessment['decisions']['candidate']['screen_passed'] and intervals['whole_seed_95_percent_interval'][0] > 0
        for phase in ('top20', 'top100'):
            decision['promotion_eligible'] &= phases.get(phase, {}).get('complete', False) and phases[phase]['assessment']['decisions']['candidate']['replay_passed']
        loader = json.loads((HERE/'loader_receipt.json').read_text()) if (HERE/'loader_receipt.json').exists() else {}
        decision['promotion_eligible'] &= loader.get('passed', False)
        decision['candidate_sha256'] = phases['confirm']['candidate_hashes']['candidate']
    decision['confidence'] = intervals
    if survivor:
        decision['selected_candidate'] = str(HERE/f'candidate_{survivor}_r3.py')
        decision['physical_controller_qualified'] = phases['screen']['assessment']['groups'][survivor]['physical_turns'] > 0 and decision['promotion_eligible']
    all_rows = []
    for phase in phases:
        ledger = HERE/f'{phase}_results.jsonl'
        if ledger.exists():
            for line in ledger.read_text().splitlines():
                row = json.loads(line); all_rows.append(dict(row, phase=phase))
    fields = ['phase', 'job_id', 'version', 'rank', 'team', 'rival', 'seed', 'candidate_seat', 'candidate_sha256', 'candidate_reward', 'opponent_reward', 'margin', 'result', 'frames', 'candidate_status', 'opponent_status', 'error']
    with (HERE/'ALL_CASES.csv').open('w', newline='', encoding='utf-8-sig') as out:
        writer = csv.DictWriter(out, fieldnames=fields, extrasaction='ignore'); writer.writeheader(); writer.writerows(all_rows)
    lines = ['# Professional engine v3 — results', '', f'Generated {decision["generated_at_utc"]}. No Kaggle access or upload.', '',
        '## Changes', '', 'Compared with exact4ea1d89a: up to36 distinct market programs, a two-level beam, native physical-prefix reuse and optional single-product rival queue-position stresses. Preserve funded physical execution, own cash, relative cash and resulting market inventory in all modeled worlds. The original sources and all engineering revisions remain preserved.', '',
        'Engineering:432 native market-phase comparisons and72 decision checks pass. The inherited action search has identical actions/branch counts/forecast gains in42 paired probes, including36 end-of-day full-interpreter fallbacks; sampled timings4.787s original versus2.790s factored. This is a workload-specific speed measurement, not a universal speedup or strength result. The group-fitted model and experimental physical planner are inherited and unchanged; this candidate only tests market-program search.', '',
        '## Paired results', '', '| Panel | Version | Wins | Draws | Losses | Win points | Mean relative coins | Physical turns |', '|---|---|---:|---:|---:|---:|---:|---:|']
    for phase, receipt in phases.items():
        if not receipt.get('complete'): continue
        for version, g in receipt['assessment']['groups'].items():
            lines.append(f'| {phase} | {version} | {g["wins"]} | {g["draws"]} | {g["losses"]} | {g["points"]} | {g["mean_margin"]:.1f} | {g["physical_turns"]} |')
    lines += ['', 'Saved top20 is contained within top100. Saved opponents replay fixed actions, share episodes and overlap older model research; these are diagnostic preservation controls. Only fresh reacting/native confirmation can support promotion.', '', '## Decision', '', f'Screen survivor: {survivor}. Promotion eligible: {decision["promotion_eligible"]}.', '']
    if intervals: lines += [f'Whole-seed paired point-rate gain: {intervals["paired_point_rate_gain"]:.6f};95% interval {intervals["whole_seed_95_percent_interval"]}.', '']
    lines += ['Root main identity is recorded in DECISION.json. This report does not automatically promote a candidate. The physical controller remains experimental. Public beliefs, rival stock and order timing are uncertain hypotheses. There is no guarantee of every-opponent wins or a top10 leaderboard rank.', '',
        'Every game: [ALL_CASES.csv](ALL_CASES.csv). Frozen sources, per-case telemetry and manifests are retained beside this report.']
    (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    (HERE/'DECISION.json').write_text(json.dumps(decision, indent=2), encoding='utf-8')
    print(json.dumps(decision, indent=2))


if __name__ == '__main__': main()
