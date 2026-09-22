"""Summarize current benchmark losses against public route signatures.

This is a read-only analysis helper.  It never invokes Kaggle submission APIs
and never modifies a candidate agent.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
from pathlib import Path


def load(path: str):
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def basename(path: str) -> str:
    return os.path.basename(path.replace("\\", "/"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", required=True)
    ap.add_argument("--capture", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()

    benchmark = load(args.benchmark)
    capture = load(args.capture)
    summary = load(args.summary)

    route_meta = {basename(row["path"]): row for row in summary}
    loss_rows = [row for row in benchmark["rows"] if row.get("result") == "loss"]
    loss_by_path = collections.defaultdict(list)
    for row in loss_rows:
        loss_by_path[basename(row["opponent_path"])].append(row)

    capture_by_path_step = collections.defaultdict(list)
    for row in capture:
        capture_by_path_step[(basename(row["path"]), row["capture_step"])].append(row)

    routes = []
    for path, rows in sorted(loss_by_path.items()):
        meta = route_meta.get(path, {})
        snapshots = []
        for step in (72, 88):
            step_rows = capture_by_path_step.get((path, step), [])
            snapshots.append(
                {
                    "step": step,
                    "rows": [
                        {
                            "seat": item["seat"],
                            "shops": item["shops"],
                            "mine_money": item["mine_money"],
                            "opponent_money": item["opponent_money"],
                            "mine_counts": item["mine_counts"],
                            "opponent_counts": item["opponent_counts"],
                            "prices": item["prices"],
                        }
                        for item in sorted(step_rows, key=lambda item: item["seat"])
                    ],
                }
            )
        routes.append(
            {
                "path": meta.get("path", path),
                "team": meta.get("team"),
                "submission_id": meta.get("submission_id"),
                "episode_id": meta.get("episode_id"),
                "seed": meta.get("seed", rows[0].get("seed")),
                "margins": [row["margin"] for row in rows],
                "snapshots": snapshots,
            }
        )

    shop_counts = collections.Counter()
    for route in routes:
        seen = set()
        for snapshot in route["snapshots"]:
            for row in snapshot["rows"]:
                seen.update(row["shops"])
        shop_counts.update(seen)

    result = {
        "benchmark_summary": benchmark.get("summary", {}),
        "loss_route_count": len(routes),
        "loss_game_count": len(loss_rows),
        "loss_shop_route_counts": dict(shop_counts),
        "loss_routes": routes,
    }
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
    print(f"loss_routes={len(routes)} loss_games={len(loss_rows)}")
    print("shop_route_counts=" + json.dumps(dict(shop_counts), sort_keys=True))
    for route in routes:
        steps = []
        for snapshot in route["snapshots"]:
            rows = snapshot["rows"]
            if not rows:
                steps.append(f"s{snapshot['step']}:missing")
                continue
            row = rows[0]
            counts = ",".join(f"{key}={value}" for key, value in sorted(row["opponent_counts"].items()))
            steps.append(
                f"s{snapshot['step']} shop={','.join(row['shops'])} "
                f"op={row['opponent_money']:.0f} counts={counts}"
            )
        print(
            f"{route['team']} seed={route['seed']} episode={route['episode_id']} "
            f"margins={[round(value) for value in route['margins']]} | "
            + " | ".join(steps)
        )


if __name__ == "__main__":
    main()
