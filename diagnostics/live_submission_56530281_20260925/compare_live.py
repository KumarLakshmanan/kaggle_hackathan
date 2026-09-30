"""Inspect market-policy differences within one public Kaggriculture replay."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("episode_id", type=int)
    parser.add_argument("--head", type=int, default=16)
    parser.add_argument("--tail", type=int, default=12)
    args = parser.parse_args()
    path = HERE / f"episode-{args.episode_id}-replay.json"
    with path.open(encoding="utf-8") as stream:
        replay = json.load(stream)
    names = replay["info"]["TeamNames"]
    ours = names.index("Lakshmanan R")
    rival = 1 - ours
    print(
        args.episode_id, names,
        "seed", replay["info"]["seed"],
        "rewards", replay["rewards"],
    )
    differences = []
    signatures = Counter()
    for index, pair in enumerate(replay["steps"]):
        our_action = pair[ours].get("action") or {}
        rival_action = pair[rival].get("action") or {}
        our_market = our_action.get("market") or []
        rival_market = rival_action.get("market") or []
        if our_market == rival_market:
            continue
        our_ops = tuple(order[0] if order else "EMPTY" for order in our_market)
        rival_ops = tuple(order[0] if order else "EMPTY" for order in rival_market)
        signatures[(our_ops, rival_ops)] += 1
        observation = pair[ours]["observation"]
        cash = [observation["farms"][seat]["money"] for seat in (ours, rival)]
        differences.append((
            index,
            f"d{observation['day'] + 1}h{observation['hour']}",
            cash[0] - cash[1],
            our_market,
            rival_market,
        ))
    print("different market turns", len(differences))
    print("top order-pattern differences")
    for (our_ops, rival_ops), count in signatures.most_common(8):
        print(count, our_ops, "|", rival_ops)
    print("first differences")
    for row in differences[: args.head]:
        print(*row)
    print("last differences")
    for row in differences[-args.tail :]:
        print(*row)


if __name__ == "__main__":
    main()
