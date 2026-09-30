"""Summarize executed economics and farm capacity in paired event traces.

This reads traces written by ``trace_paired_game_events.py``. It does not
modify an agent, replay, or simulator state.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path


def _load(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def _capacity(farm: dict) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in farm.get("tiles", []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT":
                counts[str(tile.get("crop"))] += 1
            elif tile.get("animal"):
                counts[str(tile.get("animal"))] += 1
            elif tile.get("kind") == "WEED":
                counts["WEED"] += 1
    return dict(counts)


def _economics(events: list[dict], seat: int) -> tuple[dict, dict, float]:
    receipts: dict[str, dict[str, float]] = defaultdict(lambda: {"units": 0, "cash": 0.0})
    costs: dict[str, float] = defaultdict(float)
    cash_delta = 0.0
    for event in events:
        if event.get("player") != seat or not event.get("success"):
            continue
        phase = event.get("phase")
        if phase not in ("market_unit", "market_atomic"):
            continue
        delta = float(event.get("cash_delta", float(event.get("cash_after", 0)) - float(event.get("cash_before", 0))))
        cash_delta += delta
        operation = event.get("operation")
        if operation == "SELL":
            item = str(event.get("item"))
            receipts[item]["units"] += 1
            receipts[item]["cash"] += delta
        elif delta < 0:
            item = str(event.get("item", ""))
            costs[f"{operation} {item}".strip()] -= delta
    return dict(receipts), dict(costs), cash_delta


def _daily(trace: list[dict], seat: int) -> dict[int, dict]:
    result = {}
    for frame in trace:
        step = int(frame["step"])
        if step % 24:
            continue
        observation = frame["observation"]
        farm = observation["farms"][seat]
        result[step // 24] = {
            "cash": float(farm["money"]),
            "assets": _capacity(farm),
            "shops": list(observation.get("town", {}).get("unlocked_shops", [])),
        }
    return result


def summarize(path: Path) -> None:
    data = _load(path)
    p = int(data["candidate_seat"])
    q = 1 - p
    print(f"\n{path.name}  seed={data['seed']} seat={p} margin={data['margin']:+,.0f}")
    economics = [_economics(data["events"], seat) for seat in (p, q)]
    labels = ("candidate", "opponent")
    for label, seat, (receipts, costs, delta) in zip(labels, (p, q), economics):
        final = float(data["candidate_reward"] if seat == p else data["opponent_reward"])
        start = float(data["traces"][seat][0]["observation"]["farms"][seat]["money"])
        print(f"  {label}: final={final:,.0f}, executed_cash_delta={delta:+,.0f}, cash_residual={final-start-delta:+,.0f}")
        print("    sales " + ", ".join(f"{item} {value['units']:.0f}u/${value['cash']:,.0f}" for item, value in sorted(receipts.items())))
        print("    costs " + ", ".join(f"{item} ${cash:,.0f}" for item, cash in sorted(costs.items())))
        investments: dict[tuple[int, str], int] = defaultdict(int)
        for event in data["events"]:
            if event.get("player") == seat and event.get("phase") == "market_unit" \
                    and event.get("success") and event.get("operation") in ("BUY_ANIMAL", "BUY_SEED"):
                investments[(int(event["step"]) // 24, str(event["item"]))] += 1
        print("    investments " + ", ".join(
            f"day{day}:{item}x{qty}" for (day, item), qty in sorted(investments.items())
            if item in ("GOOSE", "COW", "SHEEP", "STRAWBERRY", "TOMATO")
        ))
    daily = [_daily(data["traces"][seat], seat) for seat in (p, q)]
    for day in (0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 29):
        if day not in daily[0] or day not in daily[1]:
            continue
        a, b = daily[0][day], daily[1][day]
        print(f"  day {day:02d}: cash ${a['cash']:,.0f}/${b['cash']:,.0f}  "
              f"ours={a['assets']}  theirs={b['assets']}  shops={a['shops']}")
    final_turn = data["turns"][-1]
    for label, seat in zip(labels, (p, q)):
        ending = final_turn["players_after"][seat]
        pending = {item: qty for item, qty in ending.get("shed", {}).items() if qty}
        print(f"  {label} final shed={pending} final seed stock={ending.get('seeds', {})}")
        last = data["traces"][seat][-1]
        observation = last["observation"]
        held: dict[str, int] = defaultdict(int)
        for row in observation["farms"][seat].get("tiles", []):
            for tile in row:
                if not isinstance(tile, dict):
                    continue
                product = tile.get("crop") or {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}.get(tile.get("animal"))
                if product:
                    held[product] += int(tile.get("yield_units", 0) or 0)
        cargo: dict[str, int] = defaultdict(int)
        for inventory in observation.get("private", {}).get("inventories", []):
            for item, qty in inventory.items():
                cargo[item] += int(qty or 0)
        print(f"    step {last['step']} held on tiles={dict(held)} cargo={dict(cargo)} "
              f"quotes={observation['market'].get('prices', {})}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("traces", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.traces:
        summarize(path)


if __name__ == "__main__":
    main()
