"""Summarize matched top-100 replay results for downloaded own submissions."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
LABELS = ('ae349d83', '257f941d', '4eeac9c3')
LIMITS = (10, 50, 100)
POINTS = {'win': 1.0, 'draw': 0.5, 'loss': 0.0}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def summarize(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(row['team_id'], []).append(row)
    return {
        'teams': len(grouped), 'seats': len(rows),
        'both_seat_wins': sum(len(pair) == 2 and all(r['result'] == 'win' for r in pair)
                              for pair in grouped.values()),
        'wdl': {result: sum(r['result'] == result for r in rows)
                for result in ('win', 'draw', 'loss')},
        'mean_seat_margin': statistics.fmean(r['margin'] for r in rows),
        'median_seat_margin': statistics.median(r['margin'] for r in rows),
        'mean_own_reward': statistics.fmean(r['candidate_reward'] for r in rows),
        'mean_opponent_reward': statistics.fmean(r['opponent_reward'] for r in rows),
        'all_done_done_720': all(r['frames'] == 720 and
                                 r['candidate_status'] == r['opponent_status'] == 'DONE'
                                 for r in rows),
    }


def comparison(rows, other, limit):
    chosen = {(r['team_id'], r['candidate_seat']): r for r in rows if r['rank'] <= limit}
    baseline = {(r['team_id'], r['candidate_seat']): r for r in other if r['rank'] <= limit}
    assert chosen.keys() == baseline.keys()
    point = {key: POINTS[chosen[key]['result']] - POINTS[baseline[key]['result']]
             for key in chosen}
    margin = {key: chosen[key]['margin'] - baseline[key]['margin'] for key in chosen}
    teams = sorted({key[0] for key in chosen})
    both_seat = [sum(point[(team, seat)] for seat in (0, 1)) for team in teams]
    return {
        'seats': len(chosen),
        'improved_seats': sum(value > 0 for value in point.values()),
        'regressed_seats': sum(value < 0 for value in point.values()),
        'point_delta': sum(point.values()),
        'improved_team_pairs': sum(value > 0 for value in both_seat),
        'regressed_team_pairs': sum(value < 0 for value in both_seat),
        'mean_paired_seat_margin_delta': statistics.fmean(margin.values()),
        'median_paired_seat_margin_delta': statistics.median(margin.values()),
        'improved_margins': sum(value > 0 for value in margin.values()),
        'regressed_margins': sum(value < 0 for value in margin.values()),
    }


def main():
    receipt = json.loads((HERE / 'local_run_receipt.json').read_text(encoding='utf-8'))
    results_path = HERE / 'local_results.jsonl'
    assert receipt['complete'] and receipt['planned_games'] == receipt['completed_games'] == 600
    assert receipt['results_sha256'] == sha(results_path)
    rows = [json.loads(line) for line in results_path.read_text(encoding='utf-8').splitlines()]
    assert len(rows) == 600 and not any('error' in row for row in rows)
    assert len({(r['label'], r['team_id'], r['candidate_seat']) for r in rows}) == 600
    assert set(r['label'] for r in rows) == set(LABELS)
    entries = json.loads((HERE / 'routes/summary.json').read_text(encoding='utf-8'))
    assert len(entries) == 100 and all(e['num_actions'] == 719 for e in entries)
    by_team = {e['team_id']: e for e in entries}
    for row in rows:
        entry = by_team[row['team_id']]
        assert row['rank'] == entry['rank'] and row['seed'] == entry['seed']
        assert row['opponent_action_sha256'] == entry['action_sha256']
    by_label = {label: [r for r in rows if r['label'] == label] for label in LABELS}
    groups = {label: {f'top{n}': summarize([r for r in selected if r['rank'] <= n])
                      for n in LIMITS} for label, selected in by_label.items()}
    comparisons = {f'{left}_vs_{right}': {
        f'top{n}': comparison(by_label[left], by_label[right], n) for n in LIMITS}
        for left, right in (('ae349d83', '257f941d'), ('ae349d83', '4eeac9c3'),
                            ('257f941d', '4eeac9c3'))}
    listing = json.loads((HERE / 'submissions.json').read_text(encoding='utf-8'))
    own_ids = (56668607, 56666114, 56662188, 56609430)
    own = [{key: row.get(key) for key in ('ref', 'date', 'status', 'publicScore', 'description')}
           for sid in own_ids for row in listing if int(row['ref']) == sid]
    assert len(own) == 4
    assessment = {
        'completed_at_utc': datetime.now(timezone.utc).isoformat(),
        'leaderboard_snapshot_utc': receipt['leaderboard_snapshot_utc'],
        'source_receipt_sha256': sha(HERE / 'downloaded/download_receipt.json'),
        'local_results_sha256': receipt['results_sha256'],
        'manifest_sha256': receipt['manifest_sha256'],
        'coverage_teams': 100, 'games': 600,
        'scores_at_snapshot': own, 'groups': groups,
        'comparisons': comparisons,
        'same_hash_recent_submissions': [56668607, 56666114],
        'fixed_tape_only': True, 'independent_reactive_validation': False,
        'all_clean': all(group['all_done_done_720'] for label in groups.values()
                         for group in label.values()),
    }
    (HERE / 'assessment.json').write_text(
        json.dumps(assessment, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({
        'all_clean': assessment['all_clean'],
        'top100': {label: groups[label]['top100'] for label in LABELS},
        'comparisons': {key: value['top100'] for key, value in comparisons.items()},
    }, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
