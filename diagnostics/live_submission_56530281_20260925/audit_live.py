"""Download and summarize a bounded set of *public* Kaggle episodes.

This is read-only with respect to Kaggle. It saves downloaded public replays and
a generated JSON summary in this directory; it never submits an agent.
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
SUBMISSION = 56530281
KAGGLE = Path(
    r"C:\Users\Veeramani Selvaraj\AppData\Roaming\Python\Python314\Scripts\kaggle.exe"
)
OUR_NAME = "Lakshmanan R"


def cli(*args: str) -> str:
    result = subprocess.run(
        [str(KAGGLE), "competitions", *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def episode_ids(limit: int) -> list[int]:
    output = cli("episodes", str(SUBMISSION), "--format", "json")
    # The CLI may append a usage hint after the JSON document.
    episodes, _ = json.JSONDecoder().raw_decode(output.lstrip())
    public = [
        row
        for row in episodes
        if row["state"] == "EpisodeState.COMPLETED"
        and row["type"] == "EpisodeType.EPISODE_TYPE_PUBLIC"
    ]
    return [int(row["id"]) for row in public[:limit]]


def download(episode_id: int) -> Path | None:
    path = HERE / f"episode-{episode_id}-replay.json"
    # Kaggle can mark an episode complete before its replay payload is ready.
    # A zero-byte placeholder must be retried on the next audit.
    if path.is_file() and path.stat().st_size == 0:
        path.unlink()
    if not path.is_file():
        cli("replay", str(episode_id), "-p", str(HERE), "-q")
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size == 0:
        return None
    return path


def summarize(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        replay = json.load(stream)
    names = replay["info"]["TeamNames"]
    if names.count(OUR_NAME) != 1:
        raise ValueError(f"Expected exactly one {OUR_NAME!r} in {path.name}: {names}")
    ours = names.index(OUR_NAME)
    rival = 1 - ours
    statuses = replay["statuses"]
    rewards = replay["rewards"]
    actions = [Counter(), Counter()]
    market = [Counter(), Counter()]
    market_quantities = [Counter(), Counter()]
    matched = Counter()
    for step in replay["steps"]:
        first = step[0].get("action") or {}
        second = step[1].get("action") or {}
        matched["full"] += first == second
        matched["market"] += (first.get("market") or []) == (second.get("market") or [])
        matched["farmer"] += first.get("farmer") == second.get("farmer")
        matched["hands"] += (first.get("hands") or []) == (second.get("hands") or [])
        for seat in (0, 1):
            action = step[seat].get("action") or {}
            for unit_action in [action.get("farmer"), *(action.get("hands") or [])]:
                if isinstance(unit_action, list) and unit_action:
                    actions[seat][unit_action[0]] += 1
            for order in action.get("market") or []:
                if isinstance(order, list) and order:
                    market[seat][order[0]] += 1
                    if len(order) >= 3 and isinstance(order[2], (int, float)):
                        market_quantities[seat][f"{order[0]}:{order[1]}"] += order[2]
    daily_cash = []
    for day in range(30):
        index = min((day + 1) * 24 - 1, len(replay["steps"]) - 1)
        pair = replay["steps"][index]
        cash = [pair[seat]["observation"]["farms"][seat]["money"] for seat in (0, 1)]
        daily_cash.append([cash[ours], cash[rival]])
    own_cash = float(rewards[ours])
    rival_cash = float(rewards[rival])
    return {
        "episode_id": replay["info"]["EpisodeId"],
        "seed": replay["info"]["seed"],
        "opponent": names[rival],
        "our_seat": ours,
        "our_cash": own_cash,
        "rival_cash": rival_cash,
        "margin": own_cash - rival_cash,
        "outcome": "win" if own_cash > rival_cash else "loss" if own_cash < rival_cash else "tie",
        "our_status": statuses[ours],
        "rival_status": statuses[rival],
        "our_unit_actions": dict(actions[ours]),
        "rival_unit_actions": dict(actions[rival]),
        "our_market_orders": dict(market[ours]),
        "rival_market_orders": dict(market[rival]),
        "our_market_quantities_requested": dict(market_quantities[ours]),
        "rival_market_quantities_requested": dict(market_quantities[rival]),
        "exact_action_matches": dict(matched),
        "daily_cash_our_rival": daily_cash,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    if args.limit < 1 or args.workers < 1:
        parser.error("--limit and --workers must be positive")
    ids = episode_ids(args.limit)
    print(f"Downloading/checking {len(ids)} latest public episodes", flush=True)
    ready_ids = set()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(download, episode_id): episode_id for episode_id in ids}
        for future in as_completed(futures):
            path = future.result()
            if path is None:
                print(f"pending replay {futures[future]}", flush=True)
            else:
                ready_ids.add(futures[future])
                print(f"ready {futures[future]} {path.stat().st_size} bytes", flush=True)
    summaries = [summarize(HERE / f"episode-{episode_id}-replay.json")
                 for episode_id in ids if episode_id in ready_ids]
    output = HERE / f"audit_latest_{len(summaries)}.json"
    with output.open("w", encoding="utf-8") as stream:
        json.dump({"submission": SUBMISSION, "episodes": summaries}, stream, indent=2)
        stream.write("\n")
    counts = Counter(row["outcome"] for row in summaries)
    print(f"{counts} — {output}")
    for row in summaries:
        print(
            f"{row['episode_id']} {row['outcome']:4} "
            f"{row['margin']:+8,.0f} vs {row['opponent']} "
            f"({row['our_status']}/{row['rival_status']})"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"audit failed: {exc}", file=sys.stderr)
        raise
