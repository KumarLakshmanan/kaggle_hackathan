"""Read-only action-level late-carrot differences in selected live losses."""

from collections import Counter
import json
from pathlib import Path


SOURCE = Path(__file__).resolve().parent.parent / "live_submission_56530281_20260925"
EPISODES = (113151063, 113160599, 113161648)


def crop_counts(actions: list[dict]) -> Counter:
    counts = Counter()
    for action in actions:
        for unit in (action.get("farmer"), *(action.get("hands") or [])):
            if isinstance(unit, list) and len(unit) >= 2 and unit[0] == "PLANT":
                counts[f"PLANT_{unit[1]}"] += 1
        for order in action.get("market") or []:
            if isinstance(order, list) and len(order) >= 3 and order[0] == "BUY_SEED":
                counts[f"BUY_SEED_{order[1]}"] += max(0, int(order[2]))
    return counts


for episode_id in EPISODES:
    replay = json.loads((SOURCE / f"episode-{episode_id}-replay.json").read_text(encoding="utf-8"))
    ours = replay["info"]["TeamNames"].index("Lakshmanan R")
    actions = [
        [(step[seat].get("action") or {}) for step in replay["steps"][648:]]
        for seat in (0, 1)
    ]
    print("EPISODE", episode_id, "our_seat", ours)
    print("  late own", dict(crop_counts(actions[ours])))
    print("  late rival", dict(crop_counts(actions[1 - ours])))
    if episode_id == EPISODES[0]:
        for index in range(650, 661):
            pre = replay["steps"][index - 1][ours]["observation"]
            current = replay["steps"][index][ours]
            own_action = current.get("action") or {}
            print("  stock", index, pre["private"]["seeds"],
                  "money", pre["farms"][ours]["money"],
                  "market", own_action.get("market"),
                  "plants", [x for x in (own_action.get("farmer"), *(own_action.get("hands") or []))
                             if isinstance(x, list) and x and x[0] == "PLANT"])
    shown = 0
    for offset, step in enumerate(replay["steps"][648:]):
        own = step[ours].get("action") or {}
        rival = step[1 - ours].get("action") or {}
        own_plant = [x for x in (own.get("farmer"), *(own.get("hands") or []))
                     if isinstance(x, list) and x and x[0] == "PLANT"]
        rival_plant = [x for x in (rival.get("farmer"), *(rival.get("hands") or []))
                       if isinstance(x, list) and x and x[0] == "PLANT"]
        if own_plant != rival_plant or any(
            order[:2] == ["BUY_SEED", "CARROT"]
            for action in (own, rival) for order in (action.get("market") or [])
            if isinstance(order, list)
        ):
            print(" ", 648 + offset, "plants", own_plant, "/", rival_plant,
                  "carrot seed orders",
                  [o for o in own.get("market") or [] if isinstance(o, list) and o[:2] == ["BUY_SEED", "CARROT"]],
                  "/", [o for o in rival.get("market") or [] if isinstance(o, list) and o[:2] == ["BUY_SEED", "CARROT"]])
            shown += 1
            if shown >= 15:
                break
