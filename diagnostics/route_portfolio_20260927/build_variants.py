"""Create complete-source route-map candidates without modifying main.py."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "main.py"
EXPECTED_SHA = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
VARIANTS = {
    "icebak_110": (("ICE_CREAM_SHOP", "BAKERY"), 110),
    "icebak_123": (("ICE_CREAM_SHOP", "BAKERY"), 123),
    "bakpizza_110": (("BAKERY", "PIZZA_SHOP"), 110),
    "bakpizza_101": (("BAKERY", "PIZZA_SHOP"), 101),
}


def main() -> None:
    source = SOURCE.read_bytes()
    assert hashlib.sha256(source).hexdigest() == EXPECTED_SHA
    rows = []
    for name, (shops, route) in VARIANTS.items():
        path = ROOT / f"exp_route_{name}_20260927.py"
        suffix = (f"\n# EXPERIMENTAL 2026-09-26 complete route remapping.\n"
                  f"_R108_SHOP_ROUTES[{shops!r}] = {route}\n")
        path.write_bytes(source + suffix.encode("utf8"))
        row = {"name": name, "shops": shops, "route": route,
               "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        rows.append(row)
        print(row)
    (HERE / "variants.json").write_text(json.dumps(rows, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
