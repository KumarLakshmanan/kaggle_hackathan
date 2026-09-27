"""Full-route alternatives for the observed Yarn Store/Pizza Shop pair."""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
EXPECTED = "0e2c30f44ca7a6e0181e38a8d378af1f266ffacaaef33983a1673061797d647a"
raw = SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED
for route in (100, 123, 125):
    tail = f"""

# Experiment: complete alternate route after Yarn Store, then Pizza Shop.
_V92_TABLE[("YARN_STORE", "PIZZA_SHOP")] = {route}
"""
    dest = ROOT / f"exp_yarn_pizza_route{route}_20260926.py"
    dest.write_bytes(raw + tail.encode("utf8"))
    print(dest, hashlib.sha256(dest.read_bytes()).hexdigest())
