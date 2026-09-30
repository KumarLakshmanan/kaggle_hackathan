"""Preselect four native seeds with PIZZA_SHOP,YARN_STORE at day 6."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scan_native_yarn_seeds import first_shops

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "native_pizza_yarn_seeds.json"
START = 2609600
MAX_SCANNED = 400
NEEDED = 4


def main() -> None:
    selected = []
    scanned = []
    for seed in range(START, START + MAX_SCANNED):
        shops = first_shops(seed)
        scanned.append({"seed": seed, "shops": shops})
        if shops == ["PIZZA_SHOP", "YARN_STORE"]:
            selected.append(seed)
            print("selected", seed, shops, flush=True)
            if len(selected) == NEEDED:
                break
    payload = {"main_sha256": hashlib.sha256((ROOT / "main.py").read_bytes()).hexdigest(),
               "start": START, "selected": selected, "scanned": scanned}
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if len(selected) != NEEDED:
        raise RuntimeError(f"Found only {len(selected)} in {len(scanned)} seeds")
    print("wrote", OUT, "after", len(scanned), "seeds")


if __name__ == "__main__":
    main()
