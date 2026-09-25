"""Compare livestock capacity, service, harvest and receipts in event traces.

Diagnostics only: every quantity comes from the pre-action observation and
the interpreter's recorded unit/market events, never from intended orders.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path


PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}


def summarize(path: Path, species: str) -> None:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        data = json.load(handle)
    print(f"\n{path.name}: seed={data['seed']} margin={data['margin']:+,.0f} species={species}")
    for seat, label in ((data["candidate_seat"], "ours"), (1 - data["candidate_seat"], "rival")):
        observations = {frame["step"]: frame["observation"] for frame in data["traces"][seat]}
        counts = defaultdict(lambda: defaultdict(int))
        cohorts = defaultdict(int)
        for frame in data["traces"][seat]:
            step = frame["step"]
            if step % 24:
                continue
            farm = frame["observation"]["farms"][seat]
            for row in farm["tiles"]:
                for tile in row:
                    if isinstance(tile, dict) and tile.get("animal") == species:
                        counts[step // 24]["assets"] += 1
                        cohorts[int(tile.get("placed_day", -1))] += 1
        for event in data["events"]:
            if event.get("player") != seat or not event.get("success", event.get("changed", False)):
                continue
            step = int(event["step"])
            day = step // 24
            if event.get("phase") == "unit_action":
                action = event.get("action") or []
                if not action or action[0] not in ("HARVEST", "FEED", "CARE"):
                    continue
                obs = observations.get(step)
                if obs is None:
                    continue
                farm = obs["farms"][seat]
                actor = int(event["actor"])
                positions = [farm["farmer"], *farm["hands"]]
                if actor >= len(positions):
                    continue
                x, y = positions[actor]
                tile = farm["tiles"][y][x]
                if not isinstance(tile, dict) or tile.get("animal") != species:
                    continue
                if action[0] == "HARVEST":
                    counts[day]["harvest_actions"] += 1
                    counts[day]["harvest_units"] += int(tile.get("yield_units", 0) or 0)
                else:
                    counts[day][action[0].lower()] += 1
            elif event.get("phase") == "market_unit" and event.get("operation") == "SELL":
                if event.get("item") == PRODUCT[species]:
                    counts[day]["sold_units"] += 1
                    counts[day]["receipts"] += int(event.get("cash_delta", 0))
        total = defaultdict(int)
        for day in range(30):
            v = counts[day]
            if day >= 5:
                for key in ("harvest_actions", "harvest_units", "feed", "care", "sold_units", "receipts"):
                    total[key] += v[key]
            if v["assets"] or v["harvest_actions"] or v["sold_units"]:
                print(f"  {label:5} d{day:02} assets={v['assets']:2} feed={v['feed']:2} care={v['care']:2} "
                      f"harvest={v['harvest_actions']:2}/{v['harvest_units']:3}u "
                      f"sold={v['sold_units']:3}u cash={v['receipts']:6,}")
        print(f"  {label:5} cohorts={dict(sorted(cohorts.items()))} "
              f"totals={dict(total)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("traces", nargs="+", type=Path)
    parser.add_argument("--species", choices=tuple(PRODUCT), default="SHEEP")
    args = parser.parse_args()
    for path in args.traces:
        summarize(path, args.species)


if __name__ == "__main__":
    main()
