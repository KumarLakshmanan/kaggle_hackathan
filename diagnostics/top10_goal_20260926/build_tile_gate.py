"""Build a separate candidate that gates sale lookahead on exact farm tiles."""

import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "exp_sale_tilegate12_20260926.py"
EXPECTED = "08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863"
BEFORE = '''    return (farms[0]["tiles"] == farms[1]["tiles"]
            and farms[0]["farmer"] == farms[1]["farmer"]
            and farms[0]["hands"] == farms[1]["hands"])'''
AFTER = '''    return farms[0]["tiles"] == farms[1]["tiles"]'''

raw = SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest() == EXPECTED
source = SOURCE.read_text(encoding="utf8")
assert source.count(BEFORE) == 1
candidate = source.replace(BEFORE, AFTER)
ast.parse(candidate)
OUTPUT.write_text(candidate, encoding="utf8")
print(OUTPUT, hashlib.sha256(OUTPUT.read_bytes()).hexdigest())
