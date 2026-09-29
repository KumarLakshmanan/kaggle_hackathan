"""Two exact trajectory comparisons for the cached-input fast helper."""
from pathlib import Path
from datetime import datetime, timezone
import gzip
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.stream_replay_io_20260928 import fast_game_cached


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run():
    manifest = json.loads((HERE / 'cached_helper_manifest.json').read_text())
    for path, digest in manifest['bindings'].items():
        assert sha(path) == digest, path
    fixture = manifest['fixture']
    full = json.loads(Path(manifest['native_receipt']).read_text())
    assert full['complete'] and full['clean'] and full['passed']
    rows = []
    for seat in (0, 1):
        path = HERE / ('cached_parity_seat' + str(seat) + '.jsonl.gz')
        assert not path.exists()
        row = fast_game_cached.play(fixture, manifest['candidate'], manifest['candidate_sha256'], seat, path)
        expected = next(r for r in full['games'] if r['rival'] == fixture['fixture_id'] and r['candidate_seat'] == seat)
        fields = ('candidate_reward', 'opponent_reward', 'result', 'candidate_status', 'opponent_status', 'frames', 'candidate_telemetry')
        assert all(row[k] == expected[k] for k in fields)
        old = Path(manifest['trace_directory']) / (fixture['fixture_id'] + '_seat' + str(seat) + '.jsonl.gz')
        assert sha(old) == manifest['bindings'][str(old)]
        count = 0
        with gzip.open(old, 'rt', encoding='utf-8') as prior, gzip.open(path, 'rt', encoding='utf-8') as current:
            for left, right in zip(prior, current, strict=True):
                assert json.loads(left) == json.loads(right), (seat, count)
                count += 1
        assert count == 719 and not row['candidate_errors']
        row.update(exact_observation_action_records=count, passed=True)
        rows.append(row)
        print('Cached-input exact trajectory parity seat', seat, 'passed.', flush=True)
    for path, digest in manifest['bindings'].items():
        assert sha(path) == digest, path
    with (HERE / 'cached_helper_parity.json').open('x', encoding='utf-8') as out:
        json.dump(dict(passed=True, engineering_only=True, games=rows, manifest_sha256=sha(HERE / 'cached_helper_manifest.json'),
                       completed_at_utc=datetime.now(timezone.utc).isoformat()), out, indent=2)


if __name__ == '__main__':
    run()
