"""Build an isolated 14-turn physical-mirror sale candidate from submitted main."""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
DEST = ROOT / "exp_sale_mirror14_20260926.py"
EXPECTED = "08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863"
BEFORE = b"_ADV_LOOK = 12 if matched else 4"
AFTER = b"_ADV_LOOK = 14 if matched else 4"

raw = SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED
assert raw.count(BEFORE) == 1
DEST.write_bytes(raw.replace(BEFORE, AFTER))
print(DEST, hashlib.sha256(DEST.read_bytes()).hexdigest())
