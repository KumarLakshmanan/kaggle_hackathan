"""Compare two paired event traces on the same seed, route, and seat."""

from __future__ import annotations

import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path


def _load(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def _sales(trace: dict, player: int) -> dict[str, tuple[int, float]]:
    result = defaultdict(lambda: [0, 0.0])
    for event in trace["events"]:
        if event.get("player") == player and event.get("phase") == "market_unit" \
                and event.get("operation") == "SELL" and event.get("success"):
            row = result[event["item"]]
            row[0] += 1
            row[1] += float(event["cash_delta"])
    return {item: tuple(row) for item, row in result.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    a, b = _load(args.baseline), _load(args.candidate)
    assert a["seed"] == b["seed"] and a["candidate_seat"] == b["candidate_seat"]
    seat = int(a["candidate_seat"])
    other = 1 - seat
    print(f"margin {a['margin']:+,.0f} -> {b['margin']:+,.0f}, "
          f"own cash {a['candidate_reward']:,.0f} -> {b['candidate_reward']:,.0f}, "
          f"opponent cash {a['opponent_reward']:,.0f} -> {b['opponent_reward']:,.0f}")
    left = {int(frame["step"]): frame for frame in a["traces"][seat]}
    right = {int(frame["step"]): frame for frame in b["traces"][seat]}
    changed = [step for step in sorted(left.keys() & right.keys()) if left[step]["action"] != right[step]["action"]]
    print(f"changed candidate actions={len(changed)}")
    for step in changed[:10]:
        print(f"  step {step}: {left[step]['action']} -> {right[step]['action']}")
    for item in sorted(set(_sales(a, seat)) | set(_sales(b, seat))):
        au, ac = _sales(a, seat).get(item, (0, 0.0))
        bu, bc = _sales(b, seat).get(item, (0, 0.0))
        if au != bu or ac != bc:
            print(f"  {item} sales {au}u/${ac:,.0f} -> {bu}u/${bc:,.0f}")
    for day in range(30):
        step = day * 24
        if step not in left or step not in right:
            continue
        la = left[step]["observation"]
        rb = right[step]["observation"]
        if la["town"]["unlocked_shops"] != rb["town"]["unlocked_shops"]:
            print(f"  day {day} shop path diverged: {la['town']['unlocked_shops']} -> {rb['town']['unlocked_shops']}")
            break
    for day in (0, 6, 9, 12, 15, 18, 21, 24, 27, 29):
        step = day * 24
        if step not in left or step not in right:
            continue
        la = left[step]["observation"]["farms"]
        rb = right[step]["observation"]["farms"]
        print(f"  day {day:02d} cash delta: us {rb[seat]['money']-la[seat]['money']:+,.0f}, "
              f"opponent {rb[other]['money']-la[other]['money']:+,.0f}")


if __name__ == "__main__":
    main()
