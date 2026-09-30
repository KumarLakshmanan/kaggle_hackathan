"""Verified initial replay frames for this frozen top-100 diagnostic panel."""
import copy
import gzip
import hashlib
import json
from pathlib import Path

_CACHE = {}


def load_fixture(fixture):
    path = str(Path(fixture['source_replay_path']).resolve(strict=True))
    expected = fixture['source_replay_sha256']
    cache = _CACHE.get(path)
    if cache is None:
        raw = gzip.decompress(Path(path).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == expected
        replay = json.loads(raw)
        assert len(replay['steps']) == replay['configuration']['episodeSteps'] == 720
        assert replay['statuses'] == ['DONE', 'DONE']
        assert str(replay['module_version']) == '1.32.7'
        cache = (expected, replay['configuration'], replay['steps'][0])
        _CACHE[path] = cache
    assert cache[0] == expected
    return copy.deepcopy({'configuration': cache[1], 'steps': [cache[2]]})
