"""Build an isolated 36-turn strawberry-only physical-mirror sale pilot."""

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "exp_mirror_straw36_20260926.py"
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
OLD = "    _ADV_STRAW_EXTRA = 24 if matched else 0\n"
NEW = "    _ADV_STRAW_EXTRA = 36 if matched else 0\n"


def main():
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert source_hash == EXPECTED, source_hash
    source = SOURCE.read_text(encoding="utf8")
    assert source.count(OLD) == 1, source.count(OLD)
    candidate = source.replace(OLD, NEW)
    ast.parse(candidate)
    OUTPUT.write_text(candidate, encoding="utf8")
    print(json.dumps({"source_sha256": source_hash,
                      "candidate_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
                      "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
