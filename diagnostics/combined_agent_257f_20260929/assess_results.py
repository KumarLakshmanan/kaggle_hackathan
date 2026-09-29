"""Apply the predeclared gates and summarize already-finished comparisons."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wdl(rows, arm):
    counts = Counter(row[arm]['result'] for row in rows)
    return {k: counts[k] for k in ('win', 'draw', 'loss')}


def points(rows, arm):
    return sum({'win': 1, 'draw': .5, 'loss': 0}[row[arm]['result']] for row in rows)


def telemetry(row, arm='candidate'):
    return row[arm].get('candidate_telemetry', row.get(arm + '_raw', {}).get('candidate_telemetry', {}))


def main():
    folder = Path(sys.argv[1]).resolve(strict=True)
    manifest_path = folder / 'comparison_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    phase = manifest['phase']
    receipt_path = folder / 'comparison_manifest_receipt.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    ledger = folder / 'comparison_manifest_results.jsonl'
    assert receipt['manifest_sha256'] == sha(manifest_path)
    assert receipt['rows_sha256'] == sha(ledger)
    rows = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()]
    assert len({r['case_id'] for r in rows}) == len(rows)
    complete = receipt['status'] == 'complete' and len(rows) == len(manifest['cases'])
    clean = complete and all(r.get('execution_checks', {}).get('passed') for r in rows) and all(r[a]['candidate_status'] == 'DONE'
        and r[a]['opponent_status'] == 'DONE' and r[a]['frames'] == 720
        and not r[a]['candidate_errors'] and not r[a]['opponent_errors']
        for r in rows for a in ('baseline', 'candidate'))
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['opponent_id'] or row['group']].append(row)
    groups = {key: {
        'cases': len(rs), 'baseline_wdl': wdl(rs, 'baseline'), 'candidate_wdl': wdl(rs, 'candidate'),
        'point_delta': points(rs, 'candidate') - points(rs, 'baseline'),
        'total_margin_delta': sum(r['margin_delta'] for r in rs),
    } for key, rs in grouped.items()}
    regressions = [r['case_id'] for r in rows if r['point_delta'] < 0]
    margin_regressions = [r['case_id'] for r in rows if r['margin_delta'] < 0]
    activations = [r['case_id'] for r in rows if telemetry(r).get('a44_pizza_melon_guard_fallback72')]
    gates = {'complete': complete, 'clean_execution': clean}
    extra = {}
    if phase == 'pilot':
        targets = [r for r in rows if r['group'] == 'target']
        controls = [r for r in rows if r['group'] == 'control']
        gates.update(
            both_targets_improve=len(targets) == 2 and all(r['margin_delta'] > 0 for r in targets),
            controls_exact=len(controls) == 2 and all(all(r['baseline'][k] == r['candidate'][k]
                for k in ('result', 'candidate_reward', 'opponent_reward', 'margin')) for r in controls),
            target_activation=len(targets) == 2 and all(
                telemetry(r).get('a44_pizza_melon_guard_fallback72') is True
                and telemetry(r).get('a44_pizza_melon_guard_count72') == 12
                and telemetry(r).get('a44_goose4_route') == '' for r in targets),
            control_route=len(controls) == 2 and all(
                telemetry(r).get('a44_pizza_melon_guard_fallback72') is False
                and telemetry(r).get('a44_pizza_melon_guard_count72') == 10
                and telemetry(r).get('a44_goose4_route') == '113470868' for r in controls),
        )
    elif phase == 'saved_panel':
        sweeps = {}
        for group in ('loss30', 'top20', 'pet_public_win_control'):
            fixtures = defaultdict(list)
            for r in rows:
                if r['group'] == group:
                    fixtures[r['fixture_id']].append(r)
            sweeps[group] = {arm: sum(len(rs) == 2 and all(r[arm]['result'] == 'win' for r in rs)
                for rs in fixtures.values()) for arm in ('baseline', 'candidate')}
        gates.update(
            all_prior_winning_seats_preserved=all(r['candidate']['result'] == 'win'
                for r in rows if r['baseline']['result'] == 'win'),
            loss_sweeps_at_least_27=sweeps['loss30']['candidate'] >= 27,
            top20_sweeps_at_least_19=sweeps['top20']['candidate'] >= 19,
            saved_improvement=(points(rows, 'candidate') > points(rows, 'baseline')
                or (points(rows, 'candidate') == points(rows, 'baseline')
                    and sum(r['margin_delta'] for r in rows) > 0
                    and groups['top20']['total_margin_delta'] >= 0)),
        )
        extra['sweeps'] = sweeps
    else:
        by_seed = defaultdict(list)
        for row in rows:
            by_seed[row['seed']].append(row)
        seed_deltas = {str(seed): points(rs, 'candidate') - points(rs, 'baseline')
                       for seed, rs in by_seed.items()}
        gates.update(
            strict_pooled_point_gain=points(rows, 'candidate') > points(rows, 'baseline'),
            no_opponent_point_regression=all(g['point_delta'] >= 0 for g in groups.values()),
            at_least_three_nonnegative_seed_deltas=sum(v >= 0 for v in seed_deltas.values()) >= 3,
        )
        extra['whole_seed_point_deltas'] = seed_deltas
    result = {
        'phase': phase, 'manifest_sha256': sha(manifest_path), 'receipt_sha256': sha(receipt_path),
        'ledger_sha256': sha(ledger), 'assessor_sha256': sha(__file__),
        'candidate_sha256': manifest['candidate']['sha256'], 'cases': len(rows),
        'baseline_wdl': wdl(rows, 'baseline'), 'candidate_wdl': wdl(rows, 'candidate'),
        'point_delta': points(rows, 'candidate') - points(rows, 'baseline'),
        'total_margin_delta': sum(r['margin_delta'] for r in rows),
        'groups': groups, 'wdl_regressions': regressions, 'margin_regressions': margin_regressions,
        'pizza_guard_activations': activations, 'gates': gates, 'passed': all(gates.values()),
        'reactive_benefit_proven': phase == 'reactive' and all(gates.values()),
        'completed_at_utc': datetime.now(timezone.utc).isoformat(), **extra,
    }
    output = folder / 'assessment.json'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=True)
        stream.write('\n')
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == '__main__':
    main()
