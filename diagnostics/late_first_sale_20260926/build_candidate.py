"""Build a late-only physical-mirror first-sale advance candidate."""

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "exp_late_first_sale_mirror_20260926.py"
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
OLD = "    protected=first[1] if _ADV_PROTECT and first is not None and first[0]=='SELL' else None"
NEW = "    protected=first[1] if _ADV_PROTECT and first is not None and first[0]=='SELL' and not (_ADV_STRAW_EXTRA>0 and step>=480) else None"


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    source = SOURCE.read_text(encoding="utf-8")
    assert source.count(OLD) == 1
    candidate = source.replace(OLD, NEW)
    ast.parse(candidate)
    OUTPUT.write_text(candidate, encoding="utf-8")
    print(json.dumps({"source_sha256": EXPECTED, "candidate_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(), "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
