"""Capture public branch features for a small set of route conflicts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paired_benchmark import run_game


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--steps", nargs="+", type=int, required=True)
    parser.add_argument("--candidate", default="main.py")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    entries = {
        int(entry["seed"]): entry
        for entry in json.loads(args.summary.read_text(encoding="utf-8"))
    }
    rows = []
    for seed in args.seeds:
        entry = entries[seed]
        for seat in (0, 1):
            for step in args.steps:
                result = run_game(
                    args.candidate,
                    f"rawroute:{Path(entry['path']).resolve()}",
                    seed,
                    seat,
                    False,
                    step,
                    {},
                )
                capture = result.get("candidate_capture") or {}
                farms = capture.get("farms") or []
                mine = farms[seat] if seat < len(farms) else {}
                opponent = farms[1 - seat] if len(farms) > 1 else {}
                row = {
                            "seed": seed,
                            "seat": seat,
                            "step": step,
                            "shops": capture.get("shops", []),
                            "market_prices": capture.get("prices", {}),
                            "market_inventory": capture.get("inventory", {}),
                            "mine": mine,
                            "opponent": opponent,
                        }
                rows.append(row)
                if args.json_out is None:
                    print(json.dumps(row, separators=(",", ":")), flush=True)
    if args.json_out is not None:
        args.json_out.write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
