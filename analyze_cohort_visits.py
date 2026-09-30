"""Inspect planned worker visits to a crop cohort in a saved game trace.

Read-only diagnostic for assessing whether a crop substitution can reuse the
existing worker route. Traces come from trace_paired_game_events.py.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--crop", default="STRAWBERRY")
    parser.add_argument("--plant-day", type=int, default=11)
    parser.add_argument("--through-day", type=int, default=23)
    args = parser.parse_args()
    with gzip.open(args.trace, "rt", encoding="utf-8") as handle:
        data = json.load(handle)
    seat = int(data["candidate_seat"])
    rows = data["traces"][seat]
    positions: set[tuple[int, int]] = set()
    for row in rows:
        step = int(row["step"])
        if step // 24 != args.plant_day:
            continue
        farm = row["observation"]["farms"][seat]
        actors = [farm["farmer"], *(farm.get("hands") or [])]
        commands = [row["action"].get("farmer") or ["PASS"],
                    *(row["action"].get("hands") or [])]
        for pos, command in zip(actors, commands):
            if command[:2] == ["PLANT", args.crop]:
                positions.add((int(pos[0]), int(pos[1])))
                print(f"plant step={step} site={tuple(pos)}")
    print(f"sites={len(positions)}")
    for row in rows:
        step = int(row["step"])
        if step // 24 <= args.plant_day or step // 24 > args.through_day:
            continue
        farm = row["observation"]["farms"][seat]
        actors = [farm["farmer"], *(farm.get("hands") or [])]
        commands = [row["action"].get("farmer") or ["PASS"],
                    *(row["action"].get("hands") or [])]
        for actor, (pos, command) in enumerate(zip(actors, commands)):
            site = tuple(pos)
            if site not in positions:
                continue
            tile = farm["tiles"][site[1]][site[0]]
            if not isinstance(tile, dict):
                state = tile
            else:
                state = {key: tile.get(key) for key in
                         ("crop", "planted_day", "age", "yield_units", "watered_today")}
            print(f"step={step} day={step // 24} actor={actor} site={site} "
                  f"command={command} tile={state}")


if __name__ == "__main__":
    main()
