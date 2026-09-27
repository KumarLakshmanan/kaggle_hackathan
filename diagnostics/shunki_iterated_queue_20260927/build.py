from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

if __name__ == '__main__':
    source = ROOT / 'main.py'
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source_hash == 'c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad'
    tail = (HERE / 'tail.py').read_bytes()
    raw = source.read_bytes() + b'\n\n' + tail
    candidate = ROOT / 'exp_shunki_iterated_queue_20260927.py'
    assert not candidate.exists()
    compile(raw, str(candidate), 'exec')
    digest = hashlib.sha256(raw).hexdigest()
    backup = ROOT / f'main_candidate_iterated_queue_20260927_{digest[:8]}.py'
    assert not backup.exists()
    candidate.write_bytes(raw)
    backup.write_bytes(raw)
    result = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), candidate=str(candidate),
                  candidate_sha256=digest, backup=str(backup), source_sha256=source_hash,
                  tail_sha256=hashlib.sha256(tail).hexdigest(),
                  plan_sha256=hashlib.sha256((HERE / 'PLAN.md').read_bytes()).hexdigest(),
                  entrypoint='kaggle_iterated_queue_entrypoint')
    (HERE / 'build_manifest.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps(result, indent=2))
