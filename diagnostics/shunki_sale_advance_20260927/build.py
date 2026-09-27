import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
source = ROOT / "exp_shunki_land_retry_20260927.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == "5002b442da0d97fb66c5eca761a15f66e8d9ff6a2b6e07feaad314352065edef"
target = ROOT / "exp_shunki_sale_advance_20260927.py"
target.write_bytes(source.read_bytes() + b"\n\n" + (HERE / "layer.py").read_bytes())
raw = target.read_bytes()
compile(raw, str(target), "exec")
manifest = {"candidate_sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "plan_sha256": hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest()}
(HERE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
panel = json.loads((ROOT / "diagnostics/top50_refresh_20260927_2303/routes/summary.json").read_text(encoding="utf8"))
losses = {r["team"] for r in json.loads((ROOT / "diagnostics/top50_refresh_20260927_2303/comparison.json").read_text(encoding="utf8"))["losses"]}
(HERE / "development_routes.json").write_text(json.dumps([r for r in panel if r["team"] in losses], indent=2, ensure_ascii=False), encoding="utf8")
print(manifest)
