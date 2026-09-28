"""Build the frozen current-4ee candidate without touching main.py."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = ROOT / "main.py"
LAYER = ROOT / "diagnostics" / "shunki_land_retry_20260927" / "layer.py"
TARGET = HERE / "exp_land_retry_current_4ee.py"
EXPECTED_BASE = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"

base_bytes = BASE.read_bytes()
layer_bytes = LAYER.read_bytes()
base_hash = hashlib.sha256(base_bytes).hexdigest()
assert base_hash == EXPECTED_BASE, (base_hash, EXPECTED_BASE)

candidate_bytes = base_bytes + b"\n\n" + layer_bytes
compile(candidate_bytes, str(TARGET), "exec")
TARGET.write_bytes(candidate_bytes)
manifest = {
    "candidate_path": str(TARGET.resolve()),
    "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
    "candidate_bytes": len(candidate_bytes),
    "base_path": str(BASE.resolve()),
    "base_sha256": base_hash,
    "layer_path": str(LAYER.resolve()),
    "layer_sha256": hashlib.sha256(layer_bytes).hexdigest(),
}
(HERE / "land_retry_candidate_manifest.json").write_text(
    json.dumps(manifest, indent=2), encoding="utf-8"
)
print(json.dumps(manifest, indent=2))
