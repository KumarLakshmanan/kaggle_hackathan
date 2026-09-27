"""Count legal same-tile work at PASS turns in two saved native traces."""

from __future__ import annotations

from collections import Counter
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = ("boey_trace_s0.json.gz", "mhw_trace_s0.json.gz")
OUTPUT = HERE / "pass_opportunities_two_losses.json"
FIRST_YIELD_DAY = {"WHEAT": 2, "CARROT": 2, "TOMATO": 8,
                   "STRAWBERRY": 10, "MELON": 10}
MAX_YIELD = {"WHEAT": 6, "CARROT": 4, "TOMATO": 4,
             "STRAWBERRY": 4, "MELON": 6}
MAX_HELD = {"GOOSE": 4, "COW": 6, "SHEEP": 6}


def opportunities(tile, inv: dict, day: int) -> list[str]:
    if not isinstance(tile, dict):
        return []
    result = []
    if tile.get("kind") == "PLANT":
        if (tile.get("yield_units", 0) > 0 and
                day - tile.get("planted_day", day) >= FIRST_YIELD_DAY[tile["crop"]]):
            result.append("HARVEST")
        if not tile.get("watered_today"):
            result.append("WATER")
    elif tile.get("animal"):
        if tile.get("yield_units", 0) > 0:
            result.append("HARVEST")
        if not tile.get("cared_today"):
            result.append("CARE")
        if not tile.get("fed_today") and inv.get("WHEAT", 0) > 0:
            result.append("FEED")
        if tile.get("fertilizer_available"):
            result.append("COLLECT_FERTILIZER")
    return result


def scan(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf8") as handle:
        data = json.load(handle)
    assert data["candidate_seat"] == 0
    assert data["candidate_status"] == data["opponent_status"] == "DONE"
    traces = data["traces"][0]
    assert all(int(row["player"]) == 0 for row in traces)
    changed = {(int(e["step"]), int(e["actor"]), e["action"][0])
               for e in data["events"] if e.get("phase") == "unit_action"
               and e.get("player") == 0 and e.get("changed") and e.get("action")}
    successful: dict[tuple[int, int, int, str], list[int]] = {}
    for row in traces:
        step = int(row["step"])
        farm = row["observation"]["farms"][0]
        action = row["action"]
        commands = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
        positions = [farm["farmer"]] + list(farm["hands"])
        for actor, (command, pos) in enumerate(zip(commands, positions)):
            if command and (step, actor, command[0]) in changed:
                successful.setdefault((step // 24, pos[0], pos[1], command[0]), []).append(step)
    counts = Counter()
    bands: dict[str, Counter] = {}
    actors = Counter()
    samples = []
    distinct: dict[tuple[int, int, int, str], dict] = {}
    for row in traces:
        step = int(row["step"])
        observation = row["observation"]
        farm = observation["farms"][0]
        private = observation["private"]
        action = row["action"]
        commands = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
        positions = [farm["farmer"]] + list(farm["hands"])
        assert len(commands) == len(positions)
        assert len(private["inventories"]) >= len(positions)
        for actor, (command, pos) in enumerate(zip(commands, positions)):
            if not command or command[0] != "PASS":
                continue
            counts["pass"] += 1
            tile = farm["tiles"][pos[1]][pos[0]]
            available = opportunities(tile, private["inventories"][actor], step // 24)
            if not available:
                continue
            counts["pass_with_opportunity"] += 1
            if step < 24 * 24:
                counts["before_day24"] += 1
            band = f"{(step // 144) * 6:02d}-{(step // 144) * 6 + 5:02d}"
            bands.setdefault(band, Counter()).update(available)
            actors[str(actor)] += 1
            counts.update(available)
            for op in available:
                full = False
                if op == "HARVEST":
                    if tile.get("kind") == "PLANT":
                        full = tile.get("yield_units", 0) >= MAX_YIELD[tile["crop"]]
                    else:
                        full = tile.get("yield_units", 0) >= MAX_HELD[tile["animal"]]
                if op == "HARVEST" and not full:
                    continue
                key = (step // 24, pos[0], pos[1], op)
                distinct.setdefault(key, {"day": step // 24, "step": step,
                                          "actor": actor, "pos": pos, "op": op,
                                          "carried_wheat": private["inventories"][actor].get("WHEAT", 0),
                                          "tile_kind": tile.get("kind"),
                                          "crop": tile.get("crop"),
                                          "animal": tile.get("animal"),
                                          "yield_units": tile.get("yield_units"),
                                          "consecutive_unfed": tile.get("consecutive_unfed"),
                                          "cared_today": tile.get("cared_today")})
            if len(samples) < 18:
                samples.append({"step": step, "day": step // 24, "actor": actor,
                                "pos": pos, "tile": tile, "inventory": private["inventories"][actor],
                                "available": available})
    unique = []
    for (day, x, y, op), record in sorted(distinct.items()):
        later = [s for s in successful.get((day, x, y, op), []) if s >= record["step"]]
        unique.append({**record, "later_success_step": min(later) if later else None})
    unique_counts = Counter()
    for record in unique:
        unique_counts["unique"] += 1
        unique_counts["unique_" + record["op"]] += 1
        if record["later_success_step"] is None:
            unique_counts["unhandled_same_day"] += 1
            unique_counts["unhandled_" + record["op"]] += 1
            if record["day"] < 24:
                unique_counts["unhandled_before_day24"] += 1
    return {"trace": path.name, "candidate_reward": data["candidate_reward"],
            "opponent_reward": data["opponent_reward"], "counts": dict(counts),
            "bands": {k: dict(v) for k, v in sorted(bands.items())},
            "actors": dict(actors), "samples": samples,
            "unique_counts": dict(unique_counts), "unique": unique}


def main() -> None:
    cases = [scan(HERE / name) for name in CASES]
    OUTPUT.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf8")
    for case in cases:
        print(case["trace"], case["counts"], case["unique_counts"])
    print(OUTPUT)


if __name__ == "__main__":
    main()
