import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
source = ROOT / "exp_shunki_land_retry_20260927.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == "5002b442da0d97fb66c5eca761a15f66e8d9ff6a2b6e07feaad314352065edef"
variants = []
for name in ("timing", "crop"):
    target = ROOT / f"exp_shunki_farming_{name}_20260927.py"
    target.write_bytes(source.read_bytes() + b"\n\n" + (HERE / f"{name}_layer.py").read_bytes())
    raw = target.read_bytes()
    compile(raw, str(target), "exec")
    variants.append({"name": name, "candidate": str(target.resolve()), "sha256": hashlib.sha256(raw).hexdigest()})
(HERE / "manifest.json").write_text(json.dumps({"variants": variants, "plan_sha256": hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest()}, indent=2), encoding="utf8")
print(variants)
