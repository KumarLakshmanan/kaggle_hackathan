#!/usr/bin/env python3
"""Search one-order, one-turn market shifts against a replay route."""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import gzip
import io
import json
from pathlib import Path

from build_readable_main import build
from paired_benchmark import run_game


def read(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def write(path: Path, payload: dict) -> None:
    with path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8") as text:
                json.dump(payload, text, sort_keys=True, separators=(",", ":"))


def play(job: tuple[str, str, int, str]) -> dict:
    candidate, opponent, seed, key = job
    row = run_game(candidate, opponent, seed, 0, False, None, {})
    row["key"] = key
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--opponent", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--start-step", type=int, default=120)
    parser.add_argument("--end-step", type=int, default=717)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    base = read(args.base)
    actions = base["actions"]
    args.workdir.mkdir(parents=True, exist_ok=True)
    jobs = []
    metadata = {}
    for step in range(max(0, args.start_step), min(len(actions), args.end_step + 1)):
        market = actions[step].get("market", []) or []
        for order_index, order in enumerate(market):
            if len(order) < 3 or order[0] != "SELL":
                continue
            for delta in (-1, 1):
                target = step + delta
                if not (0 <= target < len(actions)):
                    continue
                if len(actions[target].get("market", []) or []) >= 10:
                    continue
                key = f"s{step:03d}_i{order_index}_{order[1]}_{delta:+d}"
                payload = copy.deepcopy(base)
                moved = payload["actions"][step]["market"].pop(order_index)
                payload["actions"][target].setdefault("market", []).append(moved)
                payload.setdefault("metadata", {})["single_sale_shift"] = {
                    "step": step,
                    "order_index": order_index,
                    "order": order,
                    "delta": delta,
                }
                route_path = args.workdir / f"{key}.json.gz"
                agent_path = args.workdir / f"{key}.py"
                write(route_path, payload)
                build(route_path, agent_path)
                metadata[key] = payload["metadata"]["single_sale_shift"]
                jobs.append((str(agent_path.resolve()), f"route:{args.opponent.resolve()}", args.seed, key))

    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(play, jobs):
            rows.append(row)
    rows.sort(key=lambda row: float(row["margin"]), reverse=True)
    output = [{**metadata[row["key"]], **row} for row in rows]
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps({"rows": output}, indent=2) + "\n")
    for row in output[:15]:
        print(f"margin={row['margin']:+.0f} {row['key']}")
    print(f"candidates={len(output)} winners={sum(row['margin'] > 0 for row in output)}")
    print(f"wrote={args.json_out}")


if __name__ == "__main__":
    main()
