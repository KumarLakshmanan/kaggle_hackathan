#!/usr/bin/env python3
"""Choose which early crop placements to omit after reducing opening seeds."""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import gzip
import itertools
import json
from pathlib import Path
from typing import Any

from paired_benchmark import run_game


def _read_actions(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)["actions"]


def _opening(melon_seeds: int) -> list[list[Any]]:
    return [
        ["BUY_PRODUCT", "WHEAT", 5],
        *[["HIRE"] for _ in range(5)],
        ["BUY_ANIMAL", "COW", 2],
        ["BUY_ANIMAL", "SHEEP", 2],
        ["BUY_SEED", "WHEAT", 7],
        ["BUY_SEED", "MELON", melon_seeds],
    ]


def _play(
    job: tuple[str, str, int, int, int, tuple[tuple[int, str, int], ...], dict[str, Any]]
) -> dict[str, Any]:
    route, opponent, seed, seat, melon_seeds, skipped, patches = job
    row = run_game(
        candidate=f"route:{route}",
        opponent=f"route:{opponent}",
        seed=seed,
        candidate_seat=seat,
        debug=False,
        capture_step=None,
        candidate_overrides={
            "OPENING_MARKET_OVERRIDE": _opening(melon_seeds),
            "ACTION_PATCHES": patches,
        },
    )
    return {
        "melon_seeds": melon_seeds,
        "skipped": [list(item) for item in skipped],
        "patches": patches,
        "candidate_reward": row["candidate_reward"],
        "opponent_reward": row["opponent_reward"],
        "margin": row["margin"],
        "result": row["result"],
        "candidate_status": row["candidate_status"],
        "opponent_status": row["opponent_status"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--opponent", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--seat", type=int, choices=(0, 1), default=0)
    parser.add_argument("--melon-seeds", type=int, nargs="+", default=[9, 10, 11])
    parser.add_argument(
        "--skip-count",
        type=int,
        help="Override the number of early MELON commands to mask",
    )
    parser.add_argument(
        "--fixed-action-patches",
        default="{}",
        help="JSON action patches applied to every candidate",
    )
    parser.add_argument("--opening-steps", type=int, default=24)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    try:
        fixed_patches = json.loads(args.fixed_action_patches)
    except json.JSONDecodeError as error:
        parser.error(f"invalid --fixed-action-patches JSON: {error}")
    if not isinstance(fixed_patches, dict):
        parser.error("--fixed-action-patches must decode to an object")

    route_path = args.route.resolve()
    opponent_path = args.opponent.resolve()
    actions = _read_actions(route_path)
    commands: list[tuple[int, str, int]] = []
    for step, action in enumerate(actions[: max(0, args.opening_steps)]):
        if (action.get("farmer") or ["PASS"])[:2] == ["PLANT", "MELON"]:
            commands.append((step, "farmer", -1))
        for actor, command in enumerate(action.get("hands", []) or []):
            if (command or ["PASS"])[:2] == ["PLANT", "MELON"]:
                commands.append((step, "hand", actor))
    if not commands:
        raise RuntimeError("route has no early MELON placements")

    jobs = []
    for melon_seeds in args.melon_seeds:
        skip_count = (
            int(args.skip_count)
            if args.skip_count is not None
            else len(commands) - melon_seeds
        )
        if not 0 <= skip_count <= len(commands):
            raise RuntimeError(
                f"cannot choose {melon_seeds} placements from {len(commands)} commands"
            )
        for skipped in itertools.combinations(commands, skip_count):
            patches: dict[str, Any] = copy.deepcopy(fixed_patches)
            for step, actor_kind, actor_index in skipped:
                key = str(step)
                if key not in patches:
                    patches[key] = {
                        "farmer": list(actions[step].get("farmer") or ["PASS"]),
                        "hands": [
                            list(order) for order in actions[step].get("hands", []) or []
                        ],
                        "market": [
                            list(order) for order in actions[step].get("market", []) or []
                        ],
                    }
                if actor_kind == "farmer":
                    patches[key]["farmer"] = ["PASS"]
                else:
                    patches[key]["hands"][actor_index] = ["PASS"]
            jobs.append(
                (
                    str(route_path), str(opponent_path), args.seed, args.seat,
                    melon_seeds, skipped, patches,
                )
            )

    rows = []
    best = float("-inf")
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for completed, row in enumerate(pool.map(_play, jobs), start=1):
            rows.append(row)
            if float(row["margin"]) > best:
                best = float(row["margin"])
                print(
                    f"completed={completed}/{len(jobs)} best={best:+.0f} "
                    f"melon={row['melon_seeds']} skipped={row['skipped']}",
                    flush=True,
                )

    rows.sort(key=lambda row: (-float(row["margin"]), -float(row["candidate_reward"])))
    payload = {
        "engine": "1.32.6",
        "route": str(route_path),
        "opponent": str(opponent_path),
        "seed": args.seed,
        "commands": [list(item) for item in commands],
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
