"""Build an isolated, single-file Kaggle candidate from unchanged main.py."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
WRAPPER = HERE / "wrapper.py.txt"
OUTPUT = ROOT / "exp_wool_delivery_interrupt_20260927.py"
EXPECTED_MAIN = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"


def main() -> None:
    original = MAIN.read_bytes()
    assert hashlib.sha256(original).hexdigest() == EXPECTED_MAIN
    appendix = WRAPPER.read_text(encoding="utf8")
    OUTPUT.write_bytes(original + appendix.encode("utf8"))
    print(hashlib.sha256(OUTPUT.read_bytes()).hexdigest(), OUTPUT)


if __name__ == "__main__":
    main()
