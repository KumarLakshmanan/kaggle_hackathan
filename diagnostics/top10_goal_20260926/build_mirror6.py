"""Build a standalone six-turn mirror candidate from current local main."""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "main.py"
TAIL = Path(__file__).with_name("mirror6_tail.py")
OUT = ROOT / "exp_sale_mirror6_20260926.py"
EXPECTED_BASE = "6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076"


def main() -> None:
    source = BASE.read_bytes()
    assert hashlib.sha256(source).hexdigest() == EXPECTED_BASE
    raw = source + b"\n\n" + TAIL.read_bytes()
    compile(raw, str(OUT), "exec")
    OUT.write_bytes(raw)
    print(OUT, hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
