"""Build a half-base quote variant of the frozen latched stock sale."""

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
PARENT = ROOT / "exp_mirror_stock_frontload_latched_20260927.py"
OUTPUT = ROOT / "exp_mirror_stock_frontload_halfbase_20260927.py"
SOURCE_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
PARENT_HASH = "73aa01509f6ab005e527d600b67bae108184302418b00463310d36931e3b28b2"
BEFORE = "if stock < 4 or quote <= 1:"
AFTER = "if stock < 4 or quote < 60:"


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_HASH
    assert hashlib.sha256(PARENT.read_bytes()).hexdigest() == PARENT_HASH
    candidate = PARENT.read_text(encoding="utf-8")
    assert candidate.count(BEFORE) == 1
    candidate = candidate.replace(BEFORE, AFTER)
    ast.parse(candidate)
    OUTPUT.write_text(candidate, encoding="utf-8")
    print(json.dumps({"source_sha256": SOURCE_HASH, "parent_sha256": PARENT_HASH,
                      "candidate_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
                      "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
