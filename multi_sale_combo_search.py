#!/usr/bin/env python3
"""Combine the strongest one-turn sale shifts from a prior screen."""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import gzip
import io
import itertools
import json
from pathlib import Path
from typing import Any

from paired_benchmark import run_game


def _read(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def _write(path: Path, payload: dict[str, Any]) -> None:
    with path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8") as text:
                json.dump(payload, text, sort_keys=True, separators=(",", ":"))


def _play(job: tuple[str, str, int, str]) -> dict[str, Any]:
    candidate, opponent, seed, key = job
    row = run_game(candidate, opponent, seed, 0, False, None, {})
    row["key"] = key
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--single-results", type=Path, required=True)
    parser.add_argument("--opponent", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--min-size", type=int, default=2)
    parser.add_argument("--max-size", type=int)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    base = _read(args.base.resolve())
    ranked = json.loads(args.single_results.read_text(encoding="utf-8"))["rows"]
    shifts = ranked[: max(0, args.top)]
    max_size = min(len(shifts), args.max_size or len(shifts))
    args.workdir.mkdir(parents=True, exist_ok=True)

    jobs = []
    metadata = {}
    for size in range(max(1, args.min_size), max_size + 1):
        for indices in itertools.combinations(range(len(shifts)), size):
            payload = copy.deepcopy(base)
            selected = [shifts[index] for index in indices]
            valid = True
            # Each source step in the ranked set is distinct.  Apply in source
            # step order so an append to a different target cannot disturb a
            # later original order index.
            for shift in sorted(selected, key=lambda row: int(row["step"])):
                step = int(shift["step"])
                order_index = int(shift["order_index"])
                target = step + int(shift["delta"])
                market = payload["actions"][step].get("market", []) or []
                expected = list(shift["order"])
                if order_index >= len(market) or list(market[order_index]) != expected:
                    valid = False
                    break
                moved = market.pop(order_index)
                target_market = payload["actions"][target].setdefault("market", [])
                if len(target_market) >= 10:
                    valid = False
                    break
                target_market.append(moved)
            if not valid:
                continue
            key = "__".join(str(shifts[index]["key"]) for index in indices)
            route_path = args.workdir / f"combo-{len(jobs):04d}.json.gz"
            payload.setdefault("metadata", {})["sale_shift_combo"] = selected
            _write(route_path, payload)
            metadata[key] = selected
            jobs.append(
                (
                    f"route:{route_path.resolve()}",
                    f"route:{args.opponent.resolve()}",
                    args.seed,
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
    output = [{"shifts": metadata[row["key"]], **row} for row in rows]
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps({"rows": output}, indent=2), encoding="utf-8")
    for row in output[:15]:
        print(f"margin={row['margin']:+.0f} key={row['key']}")
    print(f"candidates={len(output)} winners={sum(row['margin'] > 0 for row in output)}")
    print(f"wrote={args.json_out}")


if __name__ == "__main__":
    main()
