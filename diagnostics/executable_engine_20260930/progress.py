"""Read-only paired progress; incomplete rows are never counted as evidence."""
import argparse
from collections import Counter
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def summary(phase):
    ledger = HERE / f'{phase}_results.jsonl'
    rows = [json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
    pairs = {}
    for row in rows:
        key = (row.get('fixture_id', row.get('seed')), row['rival'], row['candidate_seat'])
        pairs.setdefault(key, {})[row['version']] = row
    complete = [p for p in pairs.values() if set(p) == {'candidate', 'baseline'}]
    points = {'win': 1, 'draw': .5, 'loss': 0}
    clean = lambda r: (not r.get('error') and not r.get('candidate_errors') and
                      not r.get('opponent_errors') and r.get('frames') == 720 and
                      r.get('candidate_status') == r.get('opponent_status') == 'DONE')
    valid = [p for p in complete if all(clean(r) for r in p.values())]
    results = {v: dict(Counter(p[v]['result'] for p in valid)) for v in ('baseline', 'candidate')}
    blocks = Counter(p['candidate']['seed'] for p in valid)
    return dict(phase=phase, recorded_cases=len(rows), completed_clean_pairs=len(valid),
                paired_results=results,
                paired_point_gain=sum(points[p['candidate']['result']] - points[p['baseline']['result']] for p in valid),
                paired_mean_margin_gain=(sum(p['candidate']['margin'] - p['baseline']['margin'] for p in valid) / len(valid) if valid else None),
                complete_eight_pair_seed_blocks=sum(n == 8 for n in blocks.values()) if phase == 'confirm' else None,
                unclean_job_ids=[r['job_id'] for r in rows if not clean(r)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('pilot', 'top20', 'top100', 'confirm'))
    print(json.dumps(summary(parser.parse_args().phase), indent=2))
