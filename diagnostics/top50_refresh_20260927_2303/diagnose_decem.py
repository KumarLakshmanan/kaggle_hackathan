"""Native farm-state trace for the fresh largest early regression."""
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module
from trace_paired_game import run


def farm_summary(farm):
    counts = Counter()
    for row in farm["tiles"]:
        for tile in row:
            if isinstance(tile, dict):
                counts[tile.get("crop") or tile.get("animal") or tile.get("kind") or "other"] += 1
    return {"cash": farm["money"], "hands": len(farm["hands"]), "tiles": dict(counts)}


def main():
    row = next(r for r in json.loads((HERE / "routes/summary.json").read_text(encoding="utf8")) if r["team"] == "DECEM")
    candidate = ROOT / "exp_shunki_ice_schedule_20260927.py"
    data = run(str(candidate), "rawroute:" + row["path"], row["seed"], 0)
    assert data["candidate_reward"] - data["opponent_reward"] == -82192
    module = _load_module(candidate, "decem_route_audit")
    snapshots = []
    try:
        for step in (72, 144, 216, 240, 288, 360, 432, 504, 576, 648, 718):
            obs = data["traces"][0][step]["observation"]
            shops = obs["town"]["unlocked_shops"]
            route = None
            for count in range(1, min(len(shops), 8) + 1):
                if step >= 72 * count:
                    route = module._DATA["route_map"].get("|".join(shops[:count]), route)
            snapshots.append({"step": step, "shops": shops, "route": route,
                              "farms": [farm_summary(f) for f in obs["farms"]],
                              "private": obs["private"], "prices": obs["market"]["prices"]})
    finally:
        sys.modules.pop(module.__name__, None)
    feed_without_wheat, animal_losses, missing_workers = [], [], []
    records = data["traces"][0]
    for index, record in enumerate(records):
        obs, action = record["observation"], record["action"]
        farm = obs["farms"][0]
        positions = [farm["farmer"]] + farm["hands"]
        inventories = obs["private"]["inventories"]
        units = [action.get("farmer", [])] + action.get("hands", [])
        if index % 24 and len(units) > len(positions):
            active_missing = sum(bool(u) and u[0] != "PASS" for u in units[len(positions):])
            if active_missing:
                missing_workers.append({"step": index, "available": len(positions), "active_missing": active_missing})
        for actor, (position, unit, inventory) in enumerate(zip(positions, units, inventories)):
            x, y = position
            tile = farm["tiles"][y][x]
            if unit and unit[0] == "FEED" and isinstance(tile, dict) and tile.get("animal") and not tile.get("fed_today") and inventory.get("WHEAT", 0) <= 0:
                feed_without_wheat.append({"step": index, "actor": actor, "position": position,
                                           "animal": tile["animal"], "shed_wheat": obs["private"]["shed"].get("WHEAT", 0),
                                           "tile": tile})
        if index + 1 < len(records):
            after = records[index + 1]["observation"]["farms"][0]
            for y, tiles in enumerate(farm["tiles"]):
                for x, tile in enumerate(tiles):
                    newer = after["tiles"][y][x]
                    if isinstance(tile, dict) and tile.get("animal") and (not isinstance(newer, dict) or newer.get("animal") != tile["animal"]):
                        animal_losses.append({"step": index, "position": [x, y], "before": tile, "after": newer})
    result = {"team": row["team"], "seed": row["seed"], "candidate_cash": data["candidate_reward"],
              "opponent_cash": data["opponent_reward"], "snapshots": snapshots,
              "feed_without_wheat": feed_without_wheat, "animal_losses": animal_losses,
              "active_commands_without_worker": missing_workers}
    (HERE / "decem_diagnosis.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    for snap in snapshots:
        print(snap["step"], snap["shops"], "route", snap["route"], "farms", snap["farms"], flush=True)
    print("feed-without-wheat", len(feed_without_wheat), feed_without_wheat[:5], flush=True)
    print("animal losses", len(animal_losses), animal_losses[:3], flush=True)
    print("active commands without worker", len(missing_workers), missing_workers[:3], flush=True)


if __name__ == "__main__":
    main()
