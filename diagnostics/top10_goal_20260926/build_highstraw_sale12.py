"""Build an isolated early-high-strawberry market-timing candidate."""

import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
DEST = ROOT / "exp_highstraw_sale12_20260926.py"
EXPECTED = "08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863"
BEFORE = b"_ADV_LOOK = 12 if matched else 4"
AFTER = b"_ADV_LOOK = 12 if matched or _highstraw_mode(observation) else 4"
MARKER = b"# Kaggle's file loader selects the last newly inserted callable in source"
HELPER = b'''# EXPERIMENT ONLY: keep day-six rival-strawberry signal for sale timing.
_HIGHSTRAW_MODE = {}

def _highstraw_mode(observation):
    try:
        step = int(observation.get('step', -1))
        seat = int(observation.get('player', 0))
        if step == 0:
            _HIGHSTRAW_MODE.pop(seat, None)
            return False
        if step == 144:
            farms = observation['farms']
            def count(farm):
                return sum(isinstance(tile, dict) and tile.get('crop') == 'STRAWBERRY'
                           for row in farm['tiles'] for tile in row)
            own = count(farms[seat])
            rival = count(farms[1-seat])
            _HIGHSTRAW_MODE[seat] = rival >= 7 and rival - own >= 3
        return bool(_HIGHSTRAW_MODE.get(seat, False))
    except Exception:
        return False

'''

raw = SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED
assert raw.count(BEFORE) == raw.count(MARKER) == 1
candidate = raw.replace(BEFORE, AFTER).replace(MARKER, HELPER + MARKER)
ast.parse(candidate.decode("utf8"))
DEST.write_bytes(candidate)
print(DEST, hashlib.sha256(candidate).hexdigest())
