"""Locate the first public signs of a high-strawberry rival in a native trace."""

import argparse
import gzip
import json
from pathlib import Path


def crop_count(farm, kind):
    total = 0
    for row in farm["tiles"]:
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == kind:
                total += 1
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    args = parser.parse_args()
    with gzip.open(args.trace, "rt", encoding="utf8") as stream:
        data = json.load(stream)
    traces = data["traces"]
    found = {}
    for seat in (0, 1):
        for rec in traces[seat]:
            step = rec["step"]
            action = rec["action"]
            if isinstance(action, dict):
                for order in action.get("market") or []:
                    if len(order) >= 3 and order[0] == "BUY_SEED" and order[1] == "STRAWBERRY":
                        found.setdefault(f"seat{seat}_first_strawberry_seed_buy", (step, order))
                    if len(order) >= 3 and order[0] == "BUY_ANIMAL":
                        found.setdefault(f"seat{seat}_first_animal_buy", (step, order))
                commands = [action.get("farmer"), *(action.get("hands") or [])]
                if any(cmd and cmd[0] == "PLANT" and len(cmd) > 1 and cmd[1] == "STRAWBERRY"
                       for cmd in commands):
                    found.setdefault(f"seat{seat}_first_strawberry_plant", step)
            farm = rec["observation"]["farms"][seat]
            count = crop_count(farm, "STRAWBERRY")
            if count:
                found.setdefault(f"seat{seat}_first_visible_strawberry", (step, count))
    our_seat = data["candidate_seat"]
    rival = 1 - our_seat
    for rec in traces[our_seat]:
        farms = rec["observation"]["farms"]
        own = crop_count(farms[our_seat], "STRAWBERRY")
        other = crop_count(farms[rival], "STRAWBERRY")
        if other > own:
            found.setdefault("first_visible_rival_strawberry_lead", (rec["step"], own, other))
    print(json.dumps({"trace": str(args.trace), "candidate_seat": our_seat,
                      "findings": found}, indent=2))


if __name__ == "__main__":
    main()
