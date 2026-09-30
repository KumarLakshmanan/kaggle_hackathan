"""Freeze a mirror-only 16-turn sale-advance candidate from current main.py."""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
DEST = ROOT / "exp_sale_mirror16_20260926.py"
EXPECTED = "0e2c30f44ca7a6e0181e38a8d378af1f266ffacaaef33983a1673061797d647a"
BEFORE = b"_ADV_LOOK = 12 if matched else 4"
AFTER = b"_ADV_LOOK = 16 if matched else 4"

raw = SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED
assert raw.count(BEFORE) == 1
DEST.write_bytes(raw.replace(BEFORE, AFTER))
print(DEST, hashlib.sha256(DEST.read_bytes()).hexdigest())
