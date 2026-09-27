"""Build a separate candidate gated on matching crop/animal layouts."""

import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "exp_sale_layoutgate12_20260926.py"
EXPECTED = "08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863"
BEFORE = '''    return (farms[0]["tiles"] == farms[1]["tiles"]
            and farms[0]["farmer"] == farms[1]["farmer"]
            and farms[0]["hands"] == farms[1]["hands"])'''
AFTER = '''    left, right = farms[0]["tiles"], farms[1]["tiles"]
    if len(left) != len(right):
        return False
    for row_a, row_b in zip(left, right):
        if len(row_a) != len(row_b):
            return False
        for a, b in zip(row_a, row_b):
            if isinstance(a, dict):
                if not isinstance(b, dict):
                    return False
                if any(a.get(key) != b.get(key) for key in ("kind", "crop", "animal")):
                    return False
            elif a != b:
                return False
    return True'''

raw = SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED
source = SOURCE.read_text(encoding="utf8")
assert source.count(BEFORE) == 1
candidate = source.replace(BEFORE, AFTER)
ast.parse(candidate)
OUTPUT.write_text(candidate, encoding="utf8")
print(OUTPUT, hashlib.sha256(OUTPUT.read_bytes()).hexdigest())
