"""Build a separate candidate with DSM's observed 144-turn public opening."""

import base64
import gzip
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
ROUTE = ROOT / "diagnostics/top100_refresh_2026-09-26" / (
    "DSM-submission-56557996-episode-113531265-seat1.json.gz")
OUTPUT = ROOT / "exp_dsm_opening_20260926.py"

with gzip.open(ROUTE, "rt", encoding="utf8") as stream:
    data = json.load(stream)
assert data["metadata"]["team"] == "DSM"
assert data["metadata"]["episode_id"] == 113531265
assert len(data["actions"]) == 719
opening = data["actions"][:144]
for action in opening:
    assert set(action) == {"farmer", "hands", "market"}

packed = base64.b85encode(zlib.compress(
    json.dumps(opening, separators=(",", ":")).encode("utf8"), 9)).decode("ascii")
addon = f'''

# EXPERIMENT ONLY: fixed opening actions observed from DSM public episode
# 113531265; subsequent routing remains observation-based. Never submit
# without a separate promotion decision and explicit user upload request.
import base64 as _dsm_b64, json as _dsm_json, zlib as _dsm_zlib
from copy import deepcopy as _dsm_copy
_DSM_PREFIX = _dsm_json.loads(_dsm_zlib.decompress(_dsm_b64.b85decode({packed!r})))
for _dsm_route in _IMPL.chassis.routes.values():
    _dsm_route[:144] = _dsm_copy(_DSM_PREFIX)
del _dsm_route
'''
OUTPUT.write_text(SOURCE.read_text(encoding="utf8") + addon, encoding="utf8")
print(json.dumps({
    "main_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "route_sha256": hashlib.sha256(ROUTE.read_bytes()).hexdigest(),
    "candidate_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
    "opening_steps": len(opening),
    "output": str(OUTPUT),
}, indent=2))
