#!/usr/bin/env python3
"""Search one-crossover hybrids between two compatible action books."""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import io
import json
from pathlib import Path
from typing import Any

from paired_benchmark import run_game


OPENING = [
    ["BUY_PRODUCT", "WHEAT", 5],
    *[["HIRE"] for _ in range(5)],
    ["BUY_ANIMAL", "COW", 2],
    ["BUY_ANIMAL", "SHEEP", 2],
    ["BUY_SEED", "WHEAT", 7],
    ["BUY_SEED", "MELON", 12],
]


def _read(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def _write(path: Path, payload: dict[str, Any]) -> None:
    with path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8") as text:
                json.dump(payload, text, sort_keys=True, separators=(",", ":"))


def _play(job: tuple[str, str, int, int, str]) -> dict[str, Any]:
    candidate, opponent, seed, seat, key = job
    row = run_game(
        candidate=candidate,
        opponent=opponent,
        seed=seed,
        candidate_seat=seat,
        debug=False,
        capture_step=None,
        candidate_overrides={"OPENING_MARKET_OVERRIDE": OPENING},
    )
    row["key"] = key
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route-a", type=Path, required=True)
    parser.add_argument("--route-b", type=Path, required=True)
    parser.add_argument("--opponent", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--seat", type=int, choices=(0, 1), default=0)
    parser.add_argument("--start", type=int, default=7)
    parser.add_argument("--end", type=int, default=168)
    parser.add_argument("--stride", type=int, default=8)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    payload_a = _read(args.route_a.resolve())
    payload_b = _read(args.route_b.resolve())
    actions_a = payload_a["actions"]
    actions_b = payload_b["actions"]
    if len(actions_a) != len(actions_b):
        raise RuntimeError("route lengths differ")
    args.workdir.mkdir(parents=True, exist_ok=True)

    jobs = []
    metadata = {}
    for threshold in range(args.start, args.end + 1, max(1, args.stride)):
        for name, left, right in (
            ("a_to_b", actions_a, actions_b),
            ("b_to_a", actions_b, actions_a),
        ):
            key = f"{name}_s{threshold:03d}"
            payload = {
                "metadata": {
                    "crossover": key,
                    "route_a": str(args.route_a.resolve()),
                    "route_b": str(args.route_b.resolve()),
                },
                "actions": [*left[:threshold], *right[threshold:]],
            }
            route_path = args.workdir / f"{key}.json.gz"
            _write(route_path, payload)
            metadata[key] = payload["metadata"]
            jobs.append(
                (
                    f"route:{route_path.resolve()}",
                    f"route:{args.opponent.resolve()}",
                    args.seed,
                    args.seat,
                    key,
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
                    f"completed={completed}/{len(jobs)} best={best:+.0f} key={row['key']}",
                    flush=True,
                )
    rows.sort(key=lambda row: float(row["margin"]), reverse=True)
    output = [{"crossover": metadata[row["key"]], **row} for row in rows]
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps({"rows": output}, indent=2), encoding="utf-8")
    for row in output[:15]:
        print(f"margin={row['margin']:+.0f} key={row['key']}")
    print(f"candidates={len(output)} winners={sum(row['margin'] > 0 for row in output)}")
    print(f"wrote={args.json_out}")


if __name__ == "__main__":
    main()
