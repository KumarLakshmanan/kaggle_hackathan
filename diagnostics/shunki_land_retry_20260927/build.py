import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
source = ROOT / "exp_shunki_ice_schedule_20260927.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == "3cc0f69fcb9f6a8bee17bf6789f0f321a17f0d47324c462def1e783d6921a603"
target = ROOT / "exp_shunki_land_retry_20260927.py"
target.write_bytes(source.read_bytes() + b"\n\n" + (HERE / "layer.py").read_bytes())
raw = target.read_bytes()
compile(raw, str(target), "exec")
manifest = {"candidate_sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "plan_sha256": hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest()}
(HERE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
print(manifest)
