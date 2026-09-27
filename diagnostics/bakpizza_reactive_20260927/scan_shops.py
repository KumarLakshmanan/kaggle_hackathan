"""Outcome-blind native seed preselection for Bakery/Pizza openings."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "diagnostics" / "top10_goal_20260926"))
from scan_native_yarn_seeds import first_shops  # noqa: E402

MAIN_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
START = 2621000
MAX_SCANNED = 1000
NEEDED = 6
TARGET = ["BAKERY", "PIZZA_SHOP"]


def main() -> None:
    assert hashlib.sha256((ROOT / "main.py").read_bytes()).hexdigest() == MAIN_HASH
    selected = []
    scanned = []
    for index, seed in enumerate(range(START, START + MAX_SCANNED), 1):
        shops = first_shops(seed)
        scanned.append({"seed": seed, "shops": shops})
        if shops == TARGET:
            selected.append(seed)
            print("selected", seed, shops, flush=True)
            if len(selected) == NEEDED:
                break
        if index % 100 == 0:
            print("scanned", index, "selected", len(selected), flush=True)
    result = {"main_sha256": MAIN_HASH, "start": START,
              "max_scanned": MAX_SCANNED, "selected": selected,
              "scanned": scanned}
    (HERE / "seed_selection.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print("scanned_total", len(scanned), "selected", selected, flush=True)
    if len(selected) != NEEDED:
        raise RuntimeError(f"Only {len(selected)} matches; six required")


if __name__ == "__main__":
    main()
