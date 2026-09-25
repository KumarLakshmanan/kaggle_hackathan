"""Read-only carrot commitment comparison on the 11 live losses.

Emitted market and unit orders are requests; only the replay's farm tiles and
the independently reconciled sale fills are treated as observed outcomes.
"""

from collections import Counter, defaultdict
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "live_submission_56530281_20260925"
evidence = json.loads((HERE / "live_clone_margin_evidence.json").read_text(encoding="utf-8"))


def carrot_tile_count(farm: dict) -> int:
    return sum(
        isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == "CARROT"
        for row in farm.get("tiles") or [] for tile in row
    )


for episode in evidence["episodes"]:
    if episode["outcome"] != "loss":
        continue
    replay = json.loads(
        (SOURCE / f"episode-{episode['episode_id']}-replay.json").read_text(encoding="utf-8")
    )
    ours = int(episode["our_seat"])
    counts = {seat: Counter() for seat in (0, 1)}
    first_plant_request_divergence = None
    first_tile_divergence = None
    for index, step in enumerate(replay["steps"]):
        for seat in (0, 1):
            action = step[seat].get("action") or {}
            for order in action.get("market") or []:
                if isinstance(order, list) and len(order) >= 3 and order[1] == "CARROT":
                    counts[seat][f"{order[0]}_CARROT_requested"] += max(0, int(order[2]))
            for unit in (action.get("farmer"), *(action.get("hands") or [])):
                if isinstance(unit, list) and unit[:2] == ["PLANT", "CARROT"]:
                    counts[seat]["PLANT_CARROT_requested"] += 1
            obs = step[seat].get("observation") or {}
            if obs:
                farm = obs["farms"][seat]
                counts[seat]["carrot_tile_turns"] += carrot_tile_count(farm)
                counts[seat]["hand_turns"] += len(farm.get("hands") or [])
        if first_plant_request_divergence is None and (
            counts[ours]["PLANT_CARROT_requested"]
            != counts[1 - ours]["PLANT_CARROT_requested"]
        ):
            first_plant_request_divergence = index
        if first_tile_divergence is None:
            pair = [step[seat].get("observation") or {} for seat in (0, 1)]
            if all(pair) and (
                carrot_tile_count(pair[ours]["farms"][ours])
                != carrot_tile_count(pair[1 - ours]["farms"][1 - ours])
            ):
                first_tile_divergence = index
    fills = defaultdict(lambda: [0, 0])
    for row in episode["model_sale_cash_by_day_item"]:
        if row["item"] == "CARROT":
            fills[int(row["seat"])][0] += int(row["filled"])
            fills[int(row["seat"])][1] += int(row["receipt"])
    shops_at_day6 = (
        replay["steps"][144][ours]["observation"].get("town", {})
        .get("unlocked_shops", [])[:2]
    )
    print(episode["episode_id"], f"margin={episode['margin']:+.0f}",
          "day6_shops", shops_at_day6,
          "first_plant_request_divergence", first_plant_request_divergence,
          "first_carrot_tile_divergence", first_tile_divergence)
    if first_plant_request_divergence is not None:
        changed_step = replay["steps"][first_plant_request_divergence]
        plant_pair = []
        for seat in (ours, 1 - ours):
            action = changed_step[seat].get("action") or {}
            plant_pair.append([
                command for command in
                (action.get("farmer"), *(action.get("hands") or []))
                if isinstance(command, list) and command[:1] == ["PLANT"]
            ])
        print("    first differing row plants ours/rival", plant_pair)
    for seat in (ours, 1 - ours):
        c = counts[seat]
        print(
            "  ", "ours" if seat == ours else "rival",
            "seed_req", c["BUY_SEED_CARROT_requested"],
            "plant_req", c["PLANT_CARROT_requested"],
            "carrot_tile_turns", c["carrot_tile_turns"],
            "hand_turns", c["hand_turns"],
            "sold", fills[seat][0],
            "receipts", fills[seat][1],
        )
