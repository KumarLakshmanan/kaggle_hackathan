"""Reproduce the remote self-play validation with the exact uploaded file."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

from kaggle_environments import make
from kaggle_environments.agent import get_last_callable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
UPLOADED = ROOT / 'main_uploaded_purchase_iterated_20260927_4eeac9c3.py'
EXPECTED_SHA = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
EPISODE = 114183268


def main():
    assert hashlib.sha256(UPLOADED.read_bytes()).hexdigest() == EXPECTED_SHA
    archive = HERE / 'raw' / f'episode-{EPISODE}-replay.json.gz'
    raw = gzip.decompress(archive.read_bytes())
    remote = json.loads(raw)
    assert remote['info']['TeamNames'] == ['Lakshmanan R', 'Lakshmanan R']
    seed = int(remote['info']['seed'])
    loaded = get_last_callable(UPLOADED.read_text(encoding='utf8'), path=str(UPLOADED)).__name__
    assert loaded == 'kaggle_purchase_iterated_entrypoint'
    env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': seed}, debug=False)
    env.run([str(UPLOADED), str(UPLOADED)])
    actions_match = [all(frame[seat].action == remote['steps'][index][seat]['action']
                         for index, frame in enumerate(env.steps[1:], 1)) for seat in (0, 1)]
    cash = [float(x.reward) for x in env.steps[-1]]
    statuses = [x.status for x in env.steps[-1]]
    row = dict(checked_at_utc=datetime.now(timezone.utc).isoformat(), episode_id=EPISODE,
               submitted_file=str(UPLOADED.resolve()), submitted_file_sha256=EXPECTED_SHA,
               loaded_callable=loaded, seed=seed, remote_replay_sha256=hashlib.sha256(raw).hexdigest(),
               remote_cash=remote['rewards'], local_cash=cash, local_statuses=statuses,
               local_frames=len(env.steps), all_719_actions_match=actions_match,
               passed=(cash == remote['rewards'] and statuses == ['DONE', 'DONE']
                       and len(env.steps) == 720 and all(actions_match)))
    (HERE / 'validation_parity.json').write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding='utf8')
    print(json.dumps(row, ensure_ascii=True), flush=True)
    assert row['passed']


if __name__ == '__main__':
    main()
