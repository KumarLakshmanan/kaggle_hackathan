import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
parent = ROOT / "exp_shunki_market_queue_20260927.py"
assert hashlib.sha256(parent.read_bytes()).hexdigest() == "a2d2869c1d53bcfcedc8514d004f73bbab27ec6ef22b34d23241e718e4c1bf47"
raw = parent.read_bytes() + b"\n\n" + (HERE / "layer.py").read_bytes()
target = ROOT / "exp_shunki_trade_quantity_20260927.py"
compile(raw, str(target), "exec")
digest = hashlib.sha256(raw).hexdigest()
assert not target.exists()
target.write_bytes(raw)
backup = ROOT / ("main_candidate_trade_quantity_20260927_" + digest[:8] + ".py")
assert not backup.exists()
backup.write_bytes(raw)
manifest = {"candidate": str(target), "candidate_sha256": digest,
            "parent_sha256": hashlib.sha256(parent.read_bytes()).hexdigest(),
            "backup": str(backup), "plan_sha256": hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest()}
(HERE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
print(json.dumps(manifest))
