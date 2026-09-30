import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
source = ROOT / "main_uploaded_shunki_schedule_20260927_3cc0f69f.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == "3cc0f69fcb9f6a8bee17bf6789f0f321a17f0d47324c462def1e783d6921a603"
target = ROOT / "exp_shunki_land_prefund_20260927.py"
raw = source.read_bytes() + b"\n\n" + (HERE / "layer.py").read_bytes()
compile(raw, str(target), "exec")
target.write_bytes(raw)
manifest = {"candidate_sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "plan_sha256": hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest()}
(HERE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
panel = json.loads((ROOT / "diagnostics/top50_refresh_20260927_2303/routes/summary.json").read_text(encoding="utf8"))
(HERE / "development_routes.json").write_text(json.dumps([r for r in panel if r["team"] == "DECEM"], indent=2), encoding="utf8")
print(manifest)
