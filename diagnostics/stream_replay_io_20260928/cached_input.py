"""Verified compact inputs for future explicitly bound diagnostic helpers."""
from pathlib import Path
import copy
import hashlib
import json

HERE = Path(__file__).resolve().parent
CACHE_PATH = HERE / 'initial_states.json'
CACHE_SHA = 'f544b134e2ad51160e4d6ad7719b9f41ad6cc850a1a51162249ede1cba279968'
_CACHE = None


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            digest.update(block)
    return digest.hexdigest()


def load_fixture(fixture):
    global _CACHE
    if file_sha(CACHE_PATH) != CACHE_SHA:
        raise ValueError('Bound initial-state cache has changed')
    if _CACHE is None:
        data = json.loads(CACHE_PATH.read_text(encoding='utf-8'))
        assert data['complete'] and data['fixture_count'] == 104
        _CACHE = ({r['source_replay_path']: r for r in data['replays']},
                  {r['fixture_id']: r['source_replay_path'] for r in data['fixtures']})
    replays, fixtures = _CACHE
    path = fixture['source_replay_path']
    if fixtures.get(fixture['fixture_id']) != path or path not in replays:
        raise ValueError('Fixture is outside the verified input cache')
    row = replays[path]
    if row['source_replay_sha256'] != fixture['source_replay_sha256']:
        raise ValueError('Fixture raw replay hash differs from audited input')
    if file_sha(path) != row['compressed_sha256']:
        raise ValueError('Original compressed replay changed after input audit')
    assert row['frame_count'] == row['configuration']['episodeSteps'] == 720
    return copy.deepcopy(dict(configuration=row['configuration'], steps=[row['initial_frame']]))
