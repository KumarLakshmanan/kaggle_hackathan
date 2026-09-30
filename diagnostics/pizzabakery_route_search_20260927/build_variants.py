"""Exact-source one-map complete route variants for Pizza/Bakery."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "main.py"
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
sys.path.insert(0, str(ROOT))
import main  # noqa: E402


def main_build() -> None:
    source = SOURCE.read_bytes()
    assert hashlib.sha256(source).hexdigest() == EXPECTED
    prefix = main._ROUTES[120][:144]
    ids = [r for r in sorted(main._ROUTES) if r != 120 and main._ROUTES[r][:144] == prefix]
    assert len(ids) == 39 and 1 not in ids
    target = HERE / "candidates"
    target.mkdir(exist_ok=True)
    rows = []
    for route in ids:
        path = target / f"route_{route}.py"
        suffix = ("\n# Isolated visible-shop complete-route experiment.\n"
                  f"_R108_SHOP_ROUTES[('PIZZA_SHOP', 'BAKERY')] = {route}\n")
        path.write_bytes(source + suffix.encode("utf8"))
        rows.append({"route": route, "path": str(path.resolve()),
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    (HERE / "variants.json").write_text(json.dumps(rows, indent=2), encoding="utf8")
    print("variants", len(rows), "ids", ids)


if __name__ == "__main__":
    main_build()
