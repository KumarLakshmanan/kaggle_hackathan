"""Read-only scan for idle, last-hour animal output that will clip overnight.

Replay row ``step`` is the observation before the action in row ``step+1``.
This is a diagnostic, not a policy input: no replay identity is used by an agent.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "live_submission_56530281_20260925"
FIRST = {"GOOSE": 4, "COW": 8, "SHEEP": 6}
INTERVAL = {"GOOSE": 1, "COW": 2, "SHEEP": 3}
MAX_HELD = {"GOOSE": 4, "COW": 6, "SHEEP": 6}


def main() -> None:
    totals: Counter[str] = Counter()
    examples = []
    for path in sorted(ROOT.glob("episode-*-replay.json")):
        replay = json.loads(path.read_text(encoding="utf-8"))
        unused_fertilizer_sites = set()
        names = replay.get("info", {}).get("TeamNames", [])
        if "Lakshmanan R" not in names:
            continue
        seat = names.index("Lakshmanan R")
        steps = replay["steps"]
        for step in range(719):
            before = steps[step][seat]["observation"]
            action = steps[step + 1][seat]["action"]
            farm = before["farms"][seat]
            positions = [farm["farmer"], *farm["hands"]]
            commands = [action.get("farmer") or ["PASS"], *(action.get("hands") or [])]
            private = before["private"]
            occupied = sum(max(0, int(n)) for n in private["shed"].values())
            occupied += sum(max(0, int(n)) for inv in private["inventories"] for n in inv.values())
            for index, (pos, command) in enumerate(zip(positions, commands)):
                if command != ["PASS"]:
                    continue
                x, y = pos
                tile = farm["tiles"][y][x]
                if not isinstance(tile, dict):
                    continue
                if (step < 696 and tile.get("animal") in FIRST
                        and tile.get("fertilizer_available")
                        and not any(other_pos == pos and other_cmd == ["COLLECT_FERTILIZER"]
                                    for other_pos, other_cmd in zip(positions, commands))):
                    totals["idle_fertilizer_collect"] += 1
                    totals[f"idle_fertilizer_hour_{step % 24}"] += 1
                    if occupied < 100:
                        totals["idle_fertilizer_capacity"] += 1
                        price = int(before["market"]["prices"].get("FERTILIZER", 0))
                        if occupied <= 85 and price >= 50:
                            totals["safe_fertilizer_any_hour"] += 1
                            site = (step // 24, x, y)
                            if site not in unused_fertilizer_sites:
                                last = min(718, (step // 24 + 1) * 24 - 1)
                                will_collect = False
                                for later in range(step + 1, last + 1):
                                    later_farm = steps[later][seat]["observation"]["farms"][seat]
                                    later_pos = [later_farm["farmer"], *later_farm["hands"]]
                                    later_act = steps[later + 1][seat]["action"]
                                    later_cmd = [later_act.get("farmer") or ["PASS"],
                                                 *(later_act.get("hands") or [])]
                                    if any(other_pos == pos and other_cmd == ["COLLECT_FERTILIZER"]
                                           for other_pos, other_cmd in zip(later_pos, later_cmd)):
                                        will_collect = True
                                        break
                                if not will_collect:
                                    unused_fertilizer_sites.add(site)
                                    totals["safe_fertilizer_uncollected_sites"] += 1
                        if step % 24 == 23:
                            totals["idle_fertilizer_last_hour"] += 1
                            totals[f"last_hour_price_{min(200, price // 25 * 25)}"] += 1
                            if occupied <= 85 and price >= 50:
                                totals["last_hour_safe_candidate"] += 1
                        if len(examples) < 12:
                            examples.append((path.stem, seat, step, index,
                                             tile.get("animal"), "FERTILIZER", occupied))
                if (tile.get("kind") == "PLANT"
                        and step // 24 - int(tile.get("planted_day", 0)) >=
                        {"WHEAT": 2, "CARROT": 2, "TOMATO": 8,
                         "STRAWBERRY": 10, "MELON": 10}.get(tile.get("crop"), 999)
                        and int(tile.get("yield_units", 0)) > 0
                        and int(tile.get("max_lifespan_step", -1)) >= 0
                        and step >= int(tile["max_lifespan_step"])
                        and (step - int(tile["max_lifespan_step"])) % 2 == 0
                        and not any(other_pos == pos and other_cmd == ["HARVEST"]
                                    for other_pos, other_cmd in zip(positions, commands))):
                    totals["idle_crop_decay"] += 1
                    if occupied + int(tile["yield_units"]) <= 100:
                        totals["idle_crop_decay_capacity"] += 1
                        if len(examples) < 12:
                            examples.append((path.stem, seat, step, index, tile.get("crop"),
                                             tile.get("yield_units", 0), occupied))
                if (step % 24 == 23 and tile.get("kind") == "PLANT" and not tile.get("watered_today")
                        and int(tile.get("consecutive_unwatered", 0)) >= 1
                        and not any(other_pos == pos and other_cmd == ["WATER"]
                                    for other_pos, other_cmd in zip(positions, commands))):
                    totals["idle_crop_would_die"] += 1
                    totals[f"idle_crop_{tile.get('crop')}"] += 1
                    if len(examples) < 12:
                        examples.append((path.stem, seat, step, index, tile.get("crop"),
                                         tile.get("yield_units", 0), occupied))
                if step % 24 != 23:
                    continue
                animal = tile.get("animal")
                if animal not in FIRST:
                    continue
                held = int(tile.get("yield_units", 0))
                if held < MAX_HELD[animal]:
                    continue
                day = step // 24
                due_age = day + 1 - int(tile.get("placed_day", 0)) - FIRST[animal]
                if due_age < 0 or due_age % INTERVAL[animal]:
                    continue
                if tile.get("consecutive_unfed", 0) >= 1 and not tile.get("fed_today"):
                    continue
                totals["exposed"] += 1
                totals[f"exposed_{animal}"] += 1
                if occupied + held <= 100:
                    totals["conservative_capacity"] += 1
                    if len(examples) < 12:
                        examples.append((path.stem, seat, step, index, animal, held, occupied))
    print(dict(totals))
    print("examples", examples)


if __name__ == "__main__":
    main()
