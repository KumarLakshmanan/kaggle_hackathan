"""Build the standalone tomato2 candidate from the exact local main and tail."""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "main.py"
TAIL = Path(__file__).with_name("tomato2_tail.py")
OUT = ROOT / "exp_v219_tomato2_20260926.py"
EXPECTED_BASE = "6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076"


def main() -> None:
    source = BASE.read_bytes()
    assert hashlib.sha256(source).hexdigest() == EXPECTED_BASE
    tail = TAIL.read_bytes()
    raw = source + b"\n\n" + tail
    compile(raw, str(OUT), "exec")
    OUT.write_bytes(raw)
    print(OUT, hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
