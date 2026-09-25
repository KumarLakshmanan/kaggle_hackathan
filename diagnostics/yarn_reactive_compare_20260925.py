"""Paired reactive comparison in worlds with the same observed first two shops.

Only the first two public shop unlocks are fixed to ICE_CREAM_SHOP,YARN_STORE.
Later shop draws remain native and may diverge when farm occupancy changes.
This is a modified-environment diagnostic, not a Kaggle rating estimate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from kaggle_environments.envs.kaggriculture import kaggriculture as engine
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paired_benchmark import run_game


DEFAULT_SEEDS = (202609251, 202609252, 202609253, 202609254)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--opponent", default="main.py")
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    original = engine._end_of_day

    def first_two_shops(state, env, day):
        result = original(state, env, day)
        if day + 1 in (3, 6):
            shops = state[0].observation.town["unlocked_shops"]
            shops[:] = ["ICE_CREAM_SHOP"] if day + 1 == 3 else [
                "ICE_CREAM_SHOP", "YARN_STORE"
            ]
        return result

    engine._end_of_day = first_two_shops
    rows = []
    try:
        for seed in args.seeds:
            for seat in (0, 1):
                baseline = run_game("main.py", args.opponent, seed, seat, False, None, {})
                candidate = run_game(
                    "exp_yarn_shop_route_20260925.py", args.opponent,
                    seed, seat, False, None,
                    {"_PAIR_FILTER": "ICE_CREAM_SHOP,YARN_STORE"},
                )
                rows.append({"seed": seed, "seat": seat, "baseline": baseline,
                             "candidate": candidate})
                print(
                    f"seed={seed} seat={seat} margin="
                    f"{baseline['margin']:+.0f}->{candidate['margin']:+.0f} "
                    f"own={baseline['candidate_reward']:.0f}->"
                    f"{candidate['candidate_reward']:.0f} "
                    f"status={candidate['candidate_status']}/"
                    f"{candidate['opponent_status']}", flush=True,
                )
    finally:
        engine._end_of_day = original

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "opponent": args.opponent,
        "seeds": list(args.seeds),
        "first_two_shops": ["ICE_CREAM_SHOP", "YARN_STORE"],
        "shop_rule": "first two forced; later native RNG",
        "rows": rows,
    }, indent=2), encoding="utf-8")
    print("wrote", args.output, flush=True)


if __name__ == "__main__":
    main()
