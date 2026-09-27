"""Predeclare the first eight native Yarn Store/Pizza Shop seeds."""

from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path

from scan_native_yarn_seeds import first_shops

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
START = 2610400
MAX_SCANNED = 768
CHUNK = 64
NEEDED = 8


def main():
    scanned = []
    selected = []
    with ProcessPoolExecutor(max_workers=8) as pool:
        for start in range(START, START + MAX_SCANNED, CHUNK):
            seeds = range(start, min(start + CHUNK, START + MAX_SCANNED))
            for seed, shops in zip(seeds, pool.map(first_shops, seeds)):
                scanned.append({"seed": seed, "shops": shops})
                if shops == ["YARN_STORE", "PIZZA_SHOP"]:
                    selected.append(seed)
                    print("selected", seed, flush=True)
                    if len(selected) >= NEEDED:
                        break
            if len(selected) >= NEEDED:
                break
    dest = HERE / "native_yarn_pizza_reverse_seeds.json"
    dest.write_text(json.dumps({
        "main_sha256": hashlib.sha256((ROOT / "main.py").read_bytes()).hexdigest(),
        "start": START, "max_scanned": MAX_SCANNED,
        "selected": selected, "scanned": scanned,
    }, indent=2), encoding="utf8")
    if len(selected) != NEEDED:
        raise RuntimeError(f"Found {len(selected)}/{NEEDED} in {len(scanned)} seeds")
    print("wrote", dest, "after", len(scanned), "seeds")


if __name__ == "__main__":
    main()
