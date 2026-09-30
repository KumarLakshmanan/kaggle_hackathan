"""Classify unsuccessful worker commands from the saved exact native traces."""

from __future__ import annotations

from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def classify(data: dict, player: int) -> dict:
    counts = Counter()
    by_action = Counter()
    by_period = defaultdict(Counter)
    examples = defaultdict(list)
    board = int(data.get("configuration", {}).get("boardSize", 10))
    # Configuration may not be preserved in the trace payload; this game is 10x10.
    board = board or 10
    for event in data["events"]:
        if event.get("phase") != "unit_action" or event.get("player") != player:
            continue
        action = event.get("action") or ["EMPTY"]
        if not action or action[0] == "PASS" or event.get("changed"):
            continue
        step, actor = int(event["step"]), int(event["actor"])
        recs = data["traces"][player]
        if step >= len(recs):
            counts["no_obs"] += 1
            continue
        obs = recs[step]["observation"]
        farm, private = obs["farms"][player], obs["private"]
        hands = farm.get("hands", [])
        pos = farm.get("farmer") if actor == 0 else (hands[actor - 1] if actor <= len(hands) else None)
        op = str(action[0])
        reason = None
        if pos is None:
            reason = "actor_absent"
        else:
            x, y = int(pos[0]), int(pos[1])
            tile = farm["tiles"][y][x]
            inventory = private.get("inventories", [{}])[actor] if actor < len(private.get("inventories", [])) else {}
            in_shed = (x in (board // 2 - 1, board // 2) and y in (board // 2 - 1, board // 2))
            if op in {"NORTH", "SOUTH", "EAST", "WEST"}:
                dx, dy = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}[op]
                reason = "move_boundary" if not (0 <= x + dx < board and 0 <= y + dy < board) else "move_other"
            elif tile == "LOCKED":
                reason = "locked_tile"
            elif op == "WATER":
                reason = "already_watered" if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("watered_today") else "not_plant"
            elif op == "HARVEST":
                reason = "empty_yield" if isinstance(tile, dict) and int(tile.get("yield_units", 0)) <= 0 else "no_harvestable_tile"
            elif op == "PLANT":
                seed = str(action[1]) if len(action) > 1 else ""
                reason = "occupied_tile" if tile is not None else ("missing_seed" if private.get("seeds", {}).get(seed, 0) <= 0 else "plant_other")
            elif op == "FERTILIZE":
                reason = "no_fertilizer" if isinstance(tile, dict) and tile.get("kind") == "PLANT" and inventory.get("FERTILIZER", 0) <= 0 else "not_plant"
            elif op == "FEED":
                reason = "not_animal" if not (isinstance(tile, dict) and "animal" in tile) else ("already_fed" if tile.get("fed_today") else ("no_wheat" if inventory.get("WHEAT", 0) <= 0 else "feed_other"))
            elif op == "CARE":
                reason = "not_animal" if not (isinstance(tile, dict) and "animal" in tile) else ("already_cared" if tile.get("cared_today") else "care_other")
            elif op == "COLLECT_FERTILIZER":
                reason = "not_animal" if not (isinstance(tile, dict) and "animal" in tile) else ("not_available" if not tile.get("fertilizer_available") else "collect_other")
            elif op == "PICKUP":
                item = str(action[1]) if len(action) > 1 else ""
                reason = "off_shed" if not in_shed else ("empty_shed" if private.get("shed", {}).get(item, 0) <= 0 else "pickup_other")
            elif op in ("DROP", "PLACE"):
                item = str(action[1]) if len(action) > 1 else ""
                has_inv = int(inventory.get(item, 0)) > 0
                if op == "DROP":
                    reason = "off_shed" if not in_shed else ("empty_inventory" if not any(int(v) > 0 for v in inventory.values()) else "drop_other")
                elif item in ("COW", "GOOSE", "SHEEP"):
                    reason = "wrong_structure" if not (isinstance(tile, dict) and tile.get("kind") == {"COW": "PASTURE", "GOOSE": "COOP", "SHEEP": "PASTURE"}[item] and "animal" not in tile) else ("empty_inventory" if not has_inv else "place_other")
                else:
                    reason = "off_shed" if not in_shed else ("empty_inventory" if not has_inv else "place_other")
            elif op == "DIG":
                reason = "empty_tile" if tile is None else ("animal_tile" if isinstance(tile, dict) and "animal" in tile else "dig_other")
            elif op in ("BUILD_COOP", "BUILD_PASTURE"):
                reason = "occupied_tile" if tile is not None else "build_other"
            else:
                reason = "other"
        counts[reason] += 1
        by_action[(op, reason)] += 1
        day = step // 24
        by_period["d00_09" if day < 10 else "d10_19" if day < 20 else "d20_29"][reason] += 1
        if len(examples[reason]) < 4:
            examples[reason].append({"step": step, "day": day, "actor": actor,
                                     "action": action, "position": pos})
    return {"total": sum(counts.values()), "by_reason": dict(counts),
            "by_action_reason": {f"{a}:{r}": n for (a, r), n in sorted(by_action.items())},
            "by_period": {p: dict(c) for p, c in by_period.items()},
            "examples": dict(examples)}


def read(path: str) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    live_name = sys.argv[1] if len(sys.argv) > 1 else "live_loss_ledgers_172258.json"
    out_name = sys.argv[2] if len(sys.argv) > 2 else "nochange_classes_172258.json"
    live = json.loads((HERE / live_name).read_text(encoding="utf-8"))
    result = {"live_losses": [], "current_top20": []}
    for row in live["rows"]:
        data = read(row["trace_path"])
        result["live_losses"].append({"episode_id": row["episode_id"], "opponent": row["opponent"],
                                       "margin": row["margin"], "own": classify(data, row["seat"]),
                                       "rival": classify(data, 1-row["seat"])})
    top20 = json.loads((HERE / "current_top20_ledgers.json").read_text(encoding="utf-8"))
    for row in top20["rows"]:
        data = read(row["trace_path"])
        result["current_top20"].append({"team": row["team"], "margin": row["margin"],
                                         "own": classify(data, 0), "rival": classify(data, 1)})
    target = HERE / out_name
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    for p, rows in result.items():
        print(p)
        for row in rows:
            own = row["own"]
            print(row.get("opponent", row.get("team")), row["margin"], own["total"], own["by_reason"])
    print("saved", target.resolve())


if __name__ == "__main__":
    main()
