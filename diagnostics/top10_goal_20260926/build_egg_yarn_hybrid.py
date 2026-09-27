"""Create full-route alternatives for the observed Brunch/Yarn shop pair."""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "main.py"
EXPECTED_MAIN = "6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076"
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == EXPECTED_MAIN

for route in (100, 101, 117):
    tail = f"""

# Experiment: one complete alternate route under visible egg-plus-yarn shops.
_EY_PAIRS = (("BRUNCH_SPOT", "YARN_STORE"), ("YARN_STORE", "BRUNCH_SPOT"))
for _ey_pair in _EY_PAIRS:
    _V92_TABLE[_ey_pair] = {route}
del _ey_pair
"""
    dest = ROOT / f"exp_egg_yarn_route{route}_20260926.py"
    dest.write_bytes(BASE.read_bytes() + tail.encode("utf8"))
    print(dest, hashlib.sha256(dest.read_bytes()).hexdigest())
