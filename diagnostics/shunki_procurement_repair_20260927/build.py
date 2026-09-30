import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
source = ROOT / "exp_shunki_land_prefund_20260927.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == "25ad35be88012af73ada8ae8230e464d53a1377f9dcc3b186d0aba6dbb78d561"
target = ROOT / "exp_shunki_procurement_repair_20260927.py"
raw = source.read_bytes()+b"\n\n"+(HERE/"layer.py").read_bytes()
compile(raw, str(target), "exec")
target.write_bytes(raw)
digest = hashlib.sha256(raw).hexdigest()
backup = ROOT / ("main_candidate_procurement_repair_20260927_"+digest[:8]+".py")
backup.write_bytes(raw)
manifest = {"candidate_sha256": digest, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "plan_sha256": hashlib.sha256((HERE/"PLAN.md").read_bytes()).hexdigest(), "backup": str(backup)}
(HERE/"manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
routes = json.loads((ROOT/"diagnostics/top50_refresh_20260927_2303/routes/summary.json").read_text(encoding="utf8"))
(HERE/"development_routes.json").write_text(json.dumps([r for r in routes if r["team"] in ("Majkel1337", "DECEM")], indent=2), encoding="utf8")
print(json.dumps(manifest))
