"""Build an experimental route-ID override after the common day-six opening."""

import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "exp_route_probe_20260926.py"
EXPECTED = "08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863"
MARKER = "# Kaggle's file loader selects the last newly inserted callable in source"
TAIL = '''
# EXPERIMENT ONLY: force an existing complete route after the common opening.
_ROUTE_PROBE_PARENT_ROUTER = _IMPL.chassis.router
_ROUTE_PROBE_ID = None
_ROUTE_PROBE_SHOPS = ('BRUNCH_SPOT', 'YARN_STORE')

def _route_probe_router(observation, step, state):
    baseline = _ROUTE_PROBE_PARENT_ROUTER(observation, step, state)
    if _ROUTE_PROBE_ID in _IMPL.chassis.routes and 144 <= step < 648:
        shops = tuple((observation.get('town') or {}).get('unlocked_shops', [])[:2])
        if shops == tuple(_ROUTE_PROBE_SHOPS):
            return _ROUTE_PROBE_ID
    return baseline

_IMPL.chassis.router = _route_probe_router

'''

raw = SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED
source = SOURCE.read_text(encoding="utf8")
assert source.count(MARKER) == 1
candidate = source.replace(MARKER, TAIL + MARKER)
ast.parse(candidate)
OUTPUT.write_text(candidate, encoding="utf8")
print(OUTPUT, hashlib.sha256(OUTPUT.read_bytes()).hexdigest())
