"""Build a direct DSM first-144-action test without changing the main artifact."""

import ast
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
OUTPUT = ROOT / "exp_dsm_direct_prefix_20260926.py"
MARKER = "# Kaggle's file loader selects the last newly inserted callable in source"

with gzip.open(ROUTE, "rt", encoding="utf8") as stream:
    data = json.load(stream)
assert data["metadata"]["team"] == "DSM"
assert len(data["actions"]) == 719
opening = data["actions"][:144]
for action in opening:
    assert set(action) == {"farmer", "hands", "market"}

packed = base64.b85encode(zlib.compress(
    json.dumps(opening, separators=(",", ":")).encode("utf8"), 9)).decode("ascii")

tail = f'''
# EXPERIMENT ONLY: direct observed DSM opening actions. The parent still runs
# on every turn to initialize its state, but its first 144 outputs are replaced.
import base64 as _dsm_b64, json as _dsm_json, zlib as _dsm_zlib
from copy import deepcopy as _dsm_copy
_DSM_DIRECT_PREFIX = _dsm_json.loads(_dsm_zlib.decompress(_dsm_b64.b85decode({packed!r})))
_DSM_DIRECT_PARENT = agent
_DSM_DIRECT_STATS = dict(dsm_direct_override=0)

def agent(observation, configuration=None):
    step = int(observation['step'])
    if step == 0:
        _DSM_DIRECT_STATS['dsm_direct_override'] = 0
    parent_action = _DSM_DIRECT_PARENT(observation, configuration)
    if step < len(_DSM_DIRECT_PREFIX):
        _DSM_DIRECT_STATS['dsm_direct_override'] += 1
        _DSM_DIRECT_STATS.update(getattr(_DSM_DIRECT_PARENT, 'telemetry', {{}}))
        return _dsm_copy(_DSM_DIRECT_PREFIX[step])
    _DSM_DIRECT_STATS.update(getattr(_DSM_DIRECT_PARENT, 'telemetry', {{}}))
    return parent_action

agent.telemetry = _DSM_DIRECT_STATS
kaggle_submission_agent = agent

'''

source = SOURCE.read_text(encoding="utf8")
assert source.count(MARKER) == 1
candidate = source.replace(MARKER, tail + MARKER)
ast.parse(candidate)
OUTPUT.write_text(candidate, encoding="utf8")
print(json.dumps({
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "route_sha256": hashlib.sha256(ROUTE.read_bytes()).hexdigest(),
    "candidate_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
    "output": str(OUTPUT),
}, indent=2))
