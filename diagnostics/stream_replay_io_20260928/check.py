"""Engineering checks and immutable initial-state cache; no policy games."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import gzip
import hashlib
import io
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.stream_replay_io_20260928.reader import load_initial, read_initial

TARGETS = ROOT / 'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
TARGETS_SHA = '524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
WINS = ROOT / 'diagnostics/partial_planting_20260928/public_win_manifest.json'
WINS_SHA = 'f1cd25bbe3e058fec3bea3bb0cc470cd135780d2bb098e701908daf4053555de'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
    return h.hexdigest()


def write(path, data):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)


def bindings():
    return dict(reader_sha256=sha(HERE / 'reader.py'), check_sha256=sha(__file__),
                plan_sha256=sha(HERE / 'PLAN.md'))


def fixtures():
    assert sha(TARGETS) == TARGETS_SHA and sha(WINS) == WINS_SHA
    targets = json.loads(TARGETS.read_text(encoding='utf-8'))
    wins = json.loads(WINS.read_text(encoding='utf-8'))
    return targets['live_losses'] + targets['current_top20'] + wins['fixtures']


def synthetic():
    frame = [dict(observation={'string': 'quoted "[{] \\ \\u1234 café 肥鱼', 'n': 12.3e-15}), {}]
    steps = [frame, [{'reward': -3000.0}, {'reward': 0}]]
    cfg = dict(episodeSteps=2, seed=1234567)
    cases = []
    for order in ('steps_first', 'config_first'):
        source = dict(steps=steps, configuration=cfg) if order == 'steps_first' else dict(configuration=cfg, steps=steps)
        source['info'] = {'empty': [], 'x': None, 'yes': True, 'no': False}
        raw = (' \n' + json.dumps(source, ensure_ascii=False) + '\n \t').encode('utf-8')
        digest = hashlib.sha256(raw).hexdigest()
        for size in (1, 2, 3, 7, 31, 64, 65536):
            result = read_initial(io.BytesIO(raw), digest, size)
            assert result['initial_frame'] == frame and result['configuration'] == cfg and result['frame_count'] == 2
            cases.append(dict(order=order, chunk_size=size, passed=True))
    valid = json.dumps(dict(configuration=cfg, steps=steps)).encode()
    invalid = [valid + b' false', valid[:-1], valid.replace(b'"seed": 1234567', b'"seed": 123x'),
               valid.replace(b'"steps": [', b'"steps": [,', 1),
               valid[:-1] + b',}', valid.replace(b'"episodeSteps": 2', b'"episodeSteps": 3')]
    for raw in invalid:
        try:
            read_initial(io.BytesIO(raw), chunk_size=3)
        except (ValueError, UnicodeDecodeError):
            pass
        else:
            raise AssertionError('Malformed replay was accepted')
    try:
        read_initial(io.BytesIO(valid), '0' * 64, 3)
    except ValueError as exc:
        assert 'SHA-256' in str(exc)
    else:
        raise AssertionError('Wrong replay digest accepted')
    write(HERE / 'synthetic.json', dict(passed=True, valid_cases=cases, invalid_cases=len(invalid),
           wrong_hash_rejected=True, completed_at_utc=datetime.now(timezone.utc).isoformat(), **bindings()))
    print('Synthetic streaming input checks pass.', flush=True)


def real():
    f = fixtures()[0]
    p = Path(f['source_replay_path'])
    compressed = sha(p)
    streamed = load_initial(p, f['source_replay_sha256'], chunk_size=4096)
    raw = gzip.decompress(p.read_bytes())
    regular = json.loads(raw)
    assert streamed['configuration'] == regular['configuration']
    assert streamed['initial_frame'] == regular['steps'][0]
    assert streamed['frame_count'] == len(regular['steps'])
    assert streamed['source_replay_sha256'] == hashlib.sha256(raw).hexdigest() == f['source_replay_sha256']
    assert sha(p) == compressed
    write(HERE / 'real_parity.json', dict(passed=True, fixture_id=f['fixture_id'],
          compressed_sha256=compressed, raw_bytes=len(raw),
          peak_buffer_characters=streamed['peak_buffer_characters'],
          completed_at_utc=datetime.now(timezone.utc).isoformat(), **bindings()))
    print('Real replay exactly matches ordinary JSON loader.', flush=True)


def cache():
    check = json.loads((HERE / 'synthetic.json').read_text(encoding='utf-8'))
    assert check['passed'] and all(check[k] == v for k, v in bindings().items())
    rows = []
    seen = {}
    for fixture in fixtures():
        p = fixture['source_replay_path']
        if p not in seen:
            compressed = sha(p)
            data = load_initial(p, fixture['source_replay_sha256'])
            assert sha(p) == compressed
            data.update(source_replay_path=p, compressed_sha256=compressed)
            seen[p] = data
        assert seen[p]['source_replay_sha256'] == fixture['source_replay_sha256']
        rows.append(dict(fixture_id=fixture['fixture_id'], source_replay_path=p))
        if len(rows) % 10 == 0:
            print('Initial-state input audit', len(rows), '/104', flush=True)
    assert len(rows) == 104
    write(HERE / 'initial_states.json', dict(complete=True, fixture_count=len(rows),
          unique_replay_count=len(seen), fixtures=rows, replays=list(seen.values()),
          target_manifest_sha256=TARGETS_SHA, public_win_manifest_sha256=WINS_SHA,
          completed_at_utc=datetime.now(timezone.utc).isoformat(), **bindings()))
    print('Bounded initial-state cache complete.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('synthetic', 'real', 'cache'))
    args = parser.parse_args()
    globals()[args.phase]()
