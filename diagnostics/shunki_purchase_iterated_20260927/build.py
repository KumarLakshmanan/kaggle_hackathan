from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

if __name__ == '__main__':
    source = ROOT / 'main_candidate_purchase_queue_20260927_43d6f448.py'
    tail_path = ROOT / 'diagnostics/shunki_iterated_queue_20260927/tail.py'
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest(source) == '43d6f44806f7ce7204aa92180584f96c894653d6cb36bb9442a0425e8fbef176'
    assert digest(ROOT / 'main.py') == 'c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad'
    raw = source.read_bytes() + b'\n\n' + tail_path.read_bytes()
    raw += b'\n\ndef kaggle_purchase_iterated_entrypoint(observation, configuration=None):\n    return agent(observation, configuration)\n'
    candidate = ROOT / 'exp_shunki_purchase_iterated_20260927.py'
    assert not candidate.exists()
    compile(raw, str(candidate), 'exec')
    sha = hashlib.sha256(raw).hexdigest()
    backup = ROOT / f'main_candidate_purchase_iterated_20260927_{sha[:8]}.py'
    assert not backup.exists()
    candidate.write_bytes(raw)
    backup.write_bytes(raw)
    out = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), candidate=str(candidate),
               candidate_sha256=sha, backup=str(backup), source_sha256=digest(source),
               incumbent_sha256=digest(ROOT / 'main.py'), tail_sha256=digest(tail_path),
               plan_sha256=digest(HERE / 'PLAN.md'), entrypoint='kaggle_purchase_iterated_entrypoint',
               excluded_component='rare planned funding; its prior coverage gate failed')
    (HERE / 'build_manifest.json').write_text(json.dumps(out, indent=2), encoding='utf8')
    print(json.dumps(out, indent=2))
