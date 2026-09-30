"""Freeze a mirror-only 12-turn sale-advance candidate from current main.py."""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
DEST = ROOT / "exp_sale_mirror12_20260926.py"
EXPECTED_MAIN = "6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076"
BEFORE = "_ADV_LOOK = 8 if matched else 4"
AFTER = "_ADV_LOOK = 12 if matched else 4"

raw = SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED_MAIN
assert raw.count(BEFORE.encode("ascii")) == 1
DEST.write_bytes(raw.replace(BEFORE.encode("ascii"), AFTER.encode("ascii")))
print(DEST, hashlib.sha256(DEST.read_bytes()).hexdigest())
