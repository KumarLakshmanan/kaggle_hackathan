"""Exact step-23 field-action replay to quantify lost animal production."""

from __future__ import annotations

import copy
import gzip
import json
from collections import Counter
from pathlib import Path

from kaggle_environments.envs.kaggriculture import kaggriculture as game


ROOT = Path(__file__).resolve().parent


def audit(seed):
    with gzip.open(ROOT / f"main_seed{seed}_self_trace.json.gz", "rt", encoding="utf-8") as handle:
        trace = json.load(handle)
    rows = []
    for turn in trace["traces"][0]:
        step = turn["step"]
        if step % 24 != 23 or step >= 719:
            continue
        observation = turn["observation"]
        action = turn["action"]
        farm = copy.deepcopy(observation["farms"][0])
        private = copy.deepcopy(observation["private"])
        day = step // 24
        commands = [action["farmer"], *(action.get("hands") or [])]
        for actor, command in enumerate(commands):
            game._apply_unit_action(farm, private, actor, command, 10, day, 24, 100)
        for y, row in enumerate(farm["tiles"]):
            for x, tile in enumerate(row):
                if not isinstance(tile, dict) or tile.get("animal") not in game.ANIMALS:
                    continue
                animal = tile["animal"]
                rule = game.ANIMALS[animal]
                if not tile["fed_today"] and tile["consecutive_unfed"] >= 1:
                    continue  # escapes before production
                age = day + 1 - tile["placed_day"] - rule["first_yield_day"]
                if age < 0 or age % rule["interval"]:
                    continue
                produced = 1 + (int(tile.get("pending_care_bonus", 0)) if tile["fed_today"] else 0)
                held = int(tile.get("yield_units", 0))
                clipped = max(0, held + produced - rule["max_held"])
                if clipped:
                    rows.append({
                        "seed": seed,
                        "day": day,
                        "step": step,
                        "xy": [x, y],
                        "animal": animal,
                        "held": held,
                        "produced": produced,
                        "clipped": clipped,
                        "quote": observation["market"]["prices"][rule["product"]],
                        "positions": [farm["farmer"], *farm["hands"]],
                        "commands": commands,
                    })
    return rows


def main():
    rows = [row for seed in (0, 1, 2) for row in audit(seed)]
    by_animal = Counter()
    for row in rows:
        by_animal[row["animal"]] += row["clipped"]
    result = {"seeds": [0, 1, 2], "events": len(rows), "clipped_units": dict(by_animal), "rows": rows}
    out = ROOT / "animal_clip_audit.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print({key: value for key, value in result.items() if key != "rows"})
    print("first_rows", rows[:12])
    print(f"wrote={out}")


if __name__ == "__main__":
    main()
