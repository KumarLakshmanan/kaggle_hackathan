"""Create research route variants with selected market sales delayed."""

from __future__ import annotations

import argparse
import copy
import gzip
import io
import json
from pathlib import Path


def delay_boundary_sales(actions: list[dict], delay: int) -> list[dict]:
    result = copy.deepcopy(actions)
    pending: dict[int, list[list]] = {}
    queue: list[list] = []
    for step, action in enumerate(result):
        market = [list(order) for order in action.get("market", []) or []]
        if step > 0 and step % 24 == 0:
            moved = [order for order in market if len(order) >= 3 and order[0] == "SELL"]
            market = [order for order in market if not (len(order) >= 3 and order[0] == "SELL")]
            if moved and step + delay < len(result):
                pending.setdefault(step + delay, []).extend(moved)
        queue.extend(pending.get(step, []))
        if queue:
            room = max(0, 10 - len(market))
            market.extend(queue[:room])
            queue = queue[room:]
        action["market"] = market
    if queue:
        result[-1]["market"] = (list(result[-1].get("market") or []) + queue)[:10]
    return result


def shift_boundary_sales(
    actions: list[dict], shift: int, start_step: int = 0, end_step: int | None = None
) -> list[dict]:
    """Move every day-boundary SELL by a signed number of turns."""
    result = copy.deepcopy(actions)
    moved: dict[int, list[list]] = {}
    for step, action in enumerate(result):
        market = [list(order) for order in action.get("market", []) or []]
        if (
            step >= start_step
            and (end_step is None or step <= end_step)
            and step > 0
            and step % 24 == 0
        ):
            sells = [order for order in market if len(order) >= 3 and order[0] == "SELL"]
            market = [order for order in market if not (len(order) >= 3 and order[0] == "SELL")]
            target = step + shift
            if sells and 0 <= target < len(result):
                moved.setdefault(target, []).extend(sells)
        action["market"] = market
    queue: list[list] = []
    for step, action in enumerate(result):
        queue.extend(moved.get(step, []))
        market = list(action.get("market") or [])
        room = max(0, 10 - len(market))
        market.extend(queue[:room])
        queue = queue[room:]
        action["market"] = market
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--boundary-delay", type=int)
    parser.add_argument("--boundary-shift", type=int)
    parser.add_argument("--start-step", type=int, default=0)
    parser.add_argument("--end-step", type=int)
    args = parser.parse_args()

    with gzip.open(args.source, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    if (args.boundary_delay is None) == (args.boundary_shift is None):
        parser.error("provide exactly one of --boundary-delay or --boundary-shift")
    if args.boundary_shift is not None:
        payload["actions"] = shift_boundary_sales(
            payload["actions"], args.boundary_shift, args.start_step, args.end_step
        )
        payload.setdefault("metadata", {})["boundary_sell_shift"] = args.boundary_shift
    else:
        payload["actions"] = delay_boundary_sales(payload["actions"], args.boundary_delay)
        payload.setdefault("metadata", {})["boundary_sell_delay"] = args.boundary_delay
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    with args.destination.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8") as text:
                json.dump(payload, text, sort_keys=True, separators=(",", ":"))
    print(args.destination.resolve())


if __name__ == "__main__":
    main()
