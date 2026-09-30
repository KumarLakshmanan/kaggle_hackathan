import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
parent = ROOT / "exp_shunki_market_queue_20260927.py"
source = ROOT / "exp_shunki_shop_optimized_20260927.py"
assert hashlib.sha256(parent.read_bytes()).hexdigest() == "a2d2869c1d53bcfcedc8514d004f73bbab27ec6ef22b34d23241e718e4c1bf47"
assert hashlib.sha256(source.read_bytes()).hexdigest() == "94f0602f0a6a2d4c1af84f8caf93ee802335582485dd2f796a8c7e5a09846604"
spec = importlib.util.spec_from_file_location("frozen_local_routes", source)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
tape = module._DATA["routes"]["113563983"]
assert len(tape) == 719
packed = base64.b64encode(zlib.compress(json.dumps(tape, separators=(",", ":")).encode(), 9)).decode()
header = "\n\n_FARMICE_TAPE = json.loads(zlib.decompress(base64.b64decode(" + repr(packed) + ")))\n"
raw = parent.read_bytes() + header.encode() + (HERE / "layer.py").read_bytes()
target = ROOT / "exp_shunki_farmice_observed_20260927.py"
compile(raw, str(target), "exec")
assert not target.exists(); target.write_bytes(raw)
digest = hashlib.sha256(raw).hexdigest()
backup = ROOT / ("main_candidate_farmice_observed_20260927_" + digest[:8] + ".py")
assert not backup.exists(); backup.write_bytes(raw)
manifest = {"candidate": str(target), "candidate_sha256": digest, "backup": str(backup),
            "parent_sha256": hashlib.sha256(parent.read_bytes()).hexdigest(),
            "route_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "episode": 113563983, "plan_sha256": hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest()}
(HERE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
print(json.dumps(manifest))
