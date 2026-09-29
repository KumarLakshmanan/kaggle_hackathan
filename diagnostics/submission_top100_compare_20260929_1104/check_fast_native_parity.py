"""Compare a frozen prefix of completed native jobs with pure native transitions."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from fast_game_current import play
from run_local import SOURCES

HERE = Path(__file__).resolve().parent
FIELDS = ('candidate_reward', 'opponent_reward', 'result',
          'candidate_status', 'opponent_status', 'frames', 'candidate_telemetry')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    entries = json.loads((HERE / 'routes/summary.json').read_text(encoding='utf-8'))
    native = []
    for line in (HERE / 'local_results.jsonl').read_text(encoding='utf-8').splitlines():
        try:
            native.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    native_by_key = {(row['label'], row['rank'], row['candidate_seat']): row
                     for row in native if 'error' not in row}
    selected = [entry for entry in entries if all(
        (label, entry['rank'], seat) in native_by_key
        for label in SOURCES for seat in (0, 1))][:3]
    assert len(selected) == 3, 'Wait for three complete rank groups.'
    result = {
        'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'native_results_prefix_sha256': sha(HERE / 'local_results.jsonl'),
        'fast_source_sha256': sha(HERE / 'fast_game_current.py'),
        'fast_input_sha256': sha(HERE / 'current_input.py'),
        'selected_ranks': [entry['rank'] for entry in selected],
        'rows': [],
    }
    for entry in selected:
        fixture = {
            'fixture_id': str(entry['team_id']),
            'seed': int(entry['seed']),
            'source_replay_path': entry['replay_path'],
            'source_replay_sha256': entry['replay_sha256'],
            'source_action_tape_path': entry['path'],
            'source_opponent_action_sha256': entry['action_sha256'],
        }
        for seat in (0, 1):
            for label, (path, digest) in SOURCES.items():
                reference = native_by_key[(label, entry['rank'], seat)]
                actual = play(fixture, str(path), digest, seat)
                mismatches = [field for field in FIELDS
                              if reference.get(field) != actual.get(field)]
                result['rows'].append({
                    'rank': entry['rank'], 'team': entry['team'],
                    'label': label, 'seat': seat,
                    'mismatches': mismatches,
                    'native_reward': [reference['candidate_reward'], reference['opponent_reward']],
                    'fast_reward': [actual['candidate_reward'], actual['opponent_reward']],
                    'fast_wall_seconds': actual['wall_seconds'],
                })
                if len(result['rows']) % 6 == 0:
                    print(f"{len(result['rows'])}/18 parity checks", flush=True)
    result.update(completed_at_utc=datetime.now(timezone.utc).isoformat(),
                  passed=not any(row['mismatches'] for row in result['rows']))
    (HERE / 'fast_native_parity.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'ranks': result['selected_ranks'],
                      'runs': len(result['rows']),
                      'mismatches': [row for row in result['rows'] if row['mismatches']],
                      'mean_fast_wall_seconds': sum(r['fast_wall_seconds'] for r in result['rows']) / 18},
                     indent=2), flush=True)
    assert result['passed']


if __name__ == '__main__':
    main()
