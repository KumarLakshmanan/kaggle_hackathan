"""Apply the prospectively frozen opening pilot decision and preserve all cases."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from run_panel import HERE, sha, assess

receipt = json.loads((HERE / 'opening_pilot_jobs_receipt.json').read_text())
assert receipt['complete'] and receipt['completed_games'] == 138
freeze = json.loads((HERE / 'opening_pilot_freeze.json').read_text())
assert freeze['jobs_sha256'] == receipt['jobs_sha256']
assert freeze['plan_sha256'] == sha(HERE / 'OPENING_PILOT_PLAN.md')

def read(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]

baseline = {}
for panel in ('top100', 'public27'):
    for row in read(HERE / f'cb76_{panel}_jobs_results.jsonl'):
        key = row['fixture_id'], row['candidate_seat']
        if key in baseline:
            assert all(baseline[key][k] == row[k] for k in (
                'candidate_sha256', 'action_sha256', 'replay_sha256', 'candidate_reward', 'opponent_reward'))
        baseline[key] = row
base_path = HERE / 'opening_pilot_baseline_rows.jsonl'
assert not base_path.exists()
base_path.write_text(''.join(json.dumps(r) + '\n' for r in baseline.values()), encoding='utf-8')
rows = read(HERE / 'opening_pilot_jobs_results.jsonl')
decisions = []
for candidate in freeze['candidates']:
    label = f"opening_family{candidate['candidate_id']}"
    selected = [r for r in rows if r['label'] == label]
    assert len(selected) == 46 and {r['candidate_sha256'] for r in selected} == {candidate['sha256']}
    path = HERE / f'{label}_pilot_rows.jsonl'
    assert not path.exists()
    path.write_text(''.join(json.dumps(r) + '\n' for r in selected), encoding='utf-8')
    prefix = HERE / f'{label}_pilot_comparison'
    subprocess.run([sys.executable, '-X', 'utf8', '-B', str(HERE / 'compare_panels.py'),
                    str(base_path), str(path), str(prefix), '--context',
                    'Current-opening development pilot; fixed tapes are not independent policy validation.'],
                   check=True, capture_output=True, text=True, encoding='utf-8')
    comparison = json.loads(prefix.with_suffix('.json').read_text(encoding='utf-8'))
    stats = comparison['candidate_assessment'][label]
    public = [r for r in selected if r['dataset'] == 'public_loss3']
    public_sweeps = assess(public)[label]['all']['both_seat_wins']
    passed = (stats['all']['all_clean'] and comparison['delta_points'] > 0
              and stats['top20']['wins'] >= 32 and public_sweeps >= 1)
    decisions.append(dict(candidate_id=candidate['candidate_id'], label=label,
        path=candidate['path'], sha256=candidate['sha256'], passed=passed,
        assessment=stats, public_loss_both_seat_wins=public_sweeps,
        delta_points=comparison['delta_points'], lost_wins=len(comparison['lost_wins']),
        minimum_margin=min(r['margin'] for r in selected),
        total_points=stats['all']['wins'] + .5 * stats['all']['draws'],
        top20_points=stats['top20']['wins'] + .5 * stats['top20']['draws']))
eligible = sorted([d for d in decisions if d['passed']],
    key=lambda d: (-d['total_points'], -d['top20_points'], -d['minimum_margin'], d['candidate_id']))
result = dict(at_utc=datetime.now(timezone.utc).isoformat(),
    plan_sha256=freeze['plan_sha256'], receipt_sha256=sha(HERE / 'opening_pilot_jobs_receipt.json'),
    candidates=decisions, selected=eligible[0] if eligible else None,
    decision='Advance one exact candidate to full development.' if eligible else
             'Reject all three raw opening families at the frozen pilot gate; no promotion.')
(HERE / 'opening_pilot_decision.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
