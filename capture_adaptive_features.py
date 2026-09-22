"""Capture public branch features against an adaptive opponent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paired_benchmark import run_game


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", default="main_v44_guarded.py")
    parser.add_argument("--opponent", default="kaggle_public_dani_relay.py")
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--steps", nargs="+", type=int, default=[72, 87, 88, 144, 152, 153])
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    rows = []
    for seed in args.seeds:
        for seat in (0, 1):
            for step in args.steps:
                result = run_game(
                    str(Path(args.candidate).resolve()),
                    str(Path(args.opponent).resolve()),
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
                rows.append(
                    {
                        "seed": seed,
                        "seat": seat,
                        "step": step,
                        "shops": capture.get("shops", []),
                        "prices": capture.get("prices", {}),
                        "inventory": capture.get("inventory", {}),
                        "mine": mine,
                        "opponent": opponent,
                        "margin": result.get("margin"),
                        "result": result.get("result"),
                    }
                )
                print(
                    f"seed={seed} seat={seat} step={step} "
                    f"shops={capture.get('shops', [])} "
                    f"opponent={opponent}",
                    flush=True,
                )

    args.json_out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"wrote={args.json_out}")


if __name__ == "__main__":
    main()
