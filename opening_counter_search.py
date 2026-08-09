#!/usr/bin/env python3
"""Search compatible turn-zero portfolios against a fixed replay route.

The continuation stays fixed, so this isolates whether the shared opening of
the Kaito/Tao replay family is responsible for a known loss.  Candidates use
only legal public actions and are evaluated by the installed live engine.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path
from typing import Any

from paired_benchmark import run_game


def _opening(
    hires: int,
    cows: int,
    sheep: int,
    wheat_seeds: int,
    melon_seeds: int,
    wheat_product: int,
) -> list[list[Any]]:
    # Dynamic WHEAT is bought first; all other opening prices are fixed.
    return [
        ["BUY_PRODUCT", "WHEAT", wheat_product],
        *[["HIRE"] for _ in range(hires)],
        ["BUY_ANIMAL", "COW", cows],
        ["BUY_ANIMAL", "SHEEP", sheep],
        ["BUY_SEED", "WHEAT", wheat_seeds],
        ["BUY_SEED", "MELON", melon_seeds],
    ]


def _estimated_cost(opening: list[list[Any]]) -> int:
    hire_costs = (1, 1, 2, 3, 5, 8, 13, 21, 34)
    hires = sum(order[0] == "HIRE" for order in opening)
    total = sum(hire_costs[:hires])
    prices = {
        ("BUY_ANIMAL", "COW"): 400,
        ("BUY_ANIMAL", "SHEEP"): 500,
        ("BUY_SEED", "WHEAT"): 10,
        ("BUY_SEED", "MELON"): 80,
        ("BUY_PRODUCT", "WHEAT"): 25,
    }
    for order in opening:
        if len(order) >= 3:
            total += prices.get((order[0], order[1]), 0) * int(order[2])
    return total


def _play(
    job: tuple[str, str, int, int, list[list[Any]], dict[str, Any]]
) -> dict[str, Any]:
    route, opponent, seed, seat, opening, action_patches = job
    row = run_game(
        candidate=f"route:{route}",
        opponent=f"route:{opponent}",
        seed=seed,
        candidate_seat=seat,
        debug=False,
        capture_step=None,
        candidate_overrides={
            "OPENING_MARKET_OVERRIDE": opening,
            "ACTION_PATCHES": action_patches,
        },
    )
    return {
        "opening": opening,
        "estimated_cost": _estimated_cost(opening),
        "candidate_reward": row["candidate_reward"],
        "opponent_reward": row["opponent_reward"],
        "margin": row["margin"],
        "result": row["result"],
        "candidate_status": row["candidate_status"],
        "opponent_status": row["opponent_status"],
        "wall_seconds": row["wall_seconds"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--opponent", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--seat", type=int, choices=(0, 1), default=0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--hires", type=int, nargs="+", default=[5])
    parser.add_argument("--cows", type=int, nargs="+", default=[2])
    parser.add_argument("--sheep", type=int, nargs="+", default=[2])
    parser.add_argument("--wheat-seeds", type=int, nargs="+", default=[5, 6, 7, 8, 9])
    parser.add_argument("--melon-seeds", type=int, nargs="+", default=[9, 10, 11, 12, 13])
    parser.add_argument("--wheat-product", type=int, nargs="+", default=[3, 4, 5, 6, 7, 8, 9])
    parser.add_argument("--max-estimated-cost", type=int, default=3000)
    parser.add_argument(
        "--action-patches",
        default="{}",
        help="JSON mapping of continuation steps to partial action replacements",
    )
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    try:
        action_patches = json.loads(args.action_patches)
    except json.JSONDecodeError as error:
        parser.error(f"invalid --action-patches JSON: {error}")
    if not isinstance(action_patches, dict):
        parser.error("--action-patches must decode to an object")

    openings = []
    seen = set()
    for hires in args.hires:
        for cows in args.cows:
            for sheep in args.sheep:
                for wheat_seeds in args.wheat_seeds:
                    for melon_seeds in args.melon_seeds:
                        for wheat_product in args.wheat_product:
                            opening = _opening(
                                hires, cows, sheep, wheat_seeds, melon_seeds, wheat_product
                            )
                            key = json.dumps(opening, separators=(",", ":"))
                            if key in seen or _estimated_cost(opening) > args.max_estimated_cost:
                                continue
                            seen.add(key)
                            openings.append(opening)

    route = str(args.route.resolve())
    opponent = str(args.opponent.resolve())
    jobs = [
        (route, opponent, args.seed, args.seat, opening, action_patches)
        for opening in openings
    ]
    rows = []
    best = float("-inf")
    completed = 0
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(_play, job) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            row = future.result()
            rows.append(row)
            completed += 1
            if float(row["margin"]) > best:
                best = float(row["margin"])
                print(
                    f"completed={completed}/{len(jobs)} best={best:+.0f} "
                    f"reward={row['candidate_reward']:.0f} cost={row['estimated_cost']} "
                    f"opening={json.dumps(row['opening'], separators=(',', ':'))}",
                    flush=True,
                )

    rows.sort(key=lambda row: (-float(row["margin"]), -float(row["candidate_reward"])))
    payload = {
        "engine": "1.32.6",
        "route": route,
        "opponent": opponent,
        "seed": args.seed,
        "seat": args.seat,
        "action_patches": action_patches,
        "tested": len(rows),
        "wins": sum(float(row["margin"]) > 0 for row in rows),
        "best": rows[0] if rows else None,
        "rows": rows,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("tested", "wins", "best")}, sort_keys=True))
    print(f"wrote={args.json_out}")


if __name__ == "__main__":
    main()
