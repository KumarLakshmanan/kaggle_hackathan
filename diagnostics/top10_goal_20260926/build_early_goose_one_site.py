"""Build one-site early goose candidate from the current local main."""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = ROOT / "main.py"
TAIL = HERE / "early_goose_one_site_tail.py"
OUT = ROOT / "exp_early_goose_one_site_20260926.py"
EXPECTED_BASE = "6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076"


def main():
    source = BASE.read_bytes()
    assert hashlib.sha256(source).hexdigest() == EXPECTED_BASE
    raw = source + b"\n\n" + TAIL.read_bytes()
    compile(raw, str(OUT), "exec")
    OUT.write_bytes(raw)
    print(OUT, hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
