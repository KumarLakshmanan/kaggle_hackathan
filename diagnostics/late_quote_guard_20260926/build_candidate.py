"""Build the predeclared half-base strawberry advance guard."""

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "exp_mirror_straw_quote60_20260926.py"
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
OLD = "        if item in picked or int(prices.get(item,0))<2:continue"
NEW = "        if item in picked or int(prices.get(item,0))<(60 if item=='STRAWBERRY' and _ADV_STRAW_EXTRA>0 else 2):continue"


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
