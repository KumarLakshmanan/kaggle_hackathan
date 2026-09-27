"""Executed cash and visible production summary for preselected current losses."""

from __future__ import annotations

from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAMES = ("Boey", "keiz", "Arda")
DAYS = (0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 29)


def tile_counts(farm: dict) -> dict[str, int]:
    counts = Counter()
    for row in farm["tiles"]:
        for tile in row:
            if isinstance(tile, dict):
                kind = tile.get("kind")
                item = tile.get("crop") or tile.get("animal") or ""
                counts[f"{kind}:{item}"] += 1
    return dict(sorted(counts.items()))


def summarize(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        data = json.load(stream)
    assert data["candidate_status"] == data["opponent_status"] == "DONE"
    own = int(data["candidate_seat"])
    sale_units = [Counter(), Counter()]
    sale_cash = [Counter(), Counter()]
    cash_cost = [Counter(), Counter()]
    plants = [Counter(), Counter()]
    places = [Counter(), Counter()]
    for event in data["events"]:
        player = event.get("player")
        if player not in (0, 1):
            continue
        phase = event.get("phase")
        operation = event.get("operation")
        if phase == "market_unit" and event.get("success"):
            item = event.get("item", "")
            delta = float(event.get("cash_delta", 0))
            if operation == "SELL":
                sale_units[player][item] += 1
                sale_cash[player][item] += delta
            elif delta < 0:
                cash_cost[player][f"{operation}:{item}"] += -delta
        elif phase == "market_atomic" and event.get("success"):
            delta = float(event.get("cash_after", 0)) - float(event.get("cash_before", 0))
            if delta < 0:
                cash_cost[player][operation] += -delta
        elif phase == "unit_action" and event.get("changed"):
            action = event.get("action") or []
            if len(action) > 1 and action[0] == "PLANT":
                plants[player][str(action[1])] += 1
            if len(action) > 1 and action[0] == "PLACE":
                places[player][str(action[1])] += 1
    snapshots = []
    trace = {int(t["step"]): t["observation"] for t in data["traces"][own]}
    for day in DAYS:
        obs = trace.get(day * 24)
        if obs is None:
            continue
        farms = obs["farms"]
        snapshots.append({"day": day, "shops": obs["town"]["unlocked_shops"],
                          "own_cash": farms[own]["money"],
                          "rival_cash": farms[1 - own]["money"],
                          "own_tiles": tile_counts(farms[own]),
                          "rival_tiles": tile_counts(farms[1 - own])})
    return {"trace": str(path), "seed": data["seed"], "seat": own,
            "own_final": data["candidate_reward"], "rival_final": data["opponent_reward"],
            "margin": data["margin"],
            "own_sale_units": dict(sale_units[own]), "rival_sale_units": dict(sale_units[1 - own]),
            "own_sale_cash": dict(sale_cash[own]), "rival_sale_cash": dict(sale_cash[1 - own]),
            "own_cash_cost": dict(cash_cost[own]), "rival_cash_cost": dict(cash_cost[1 - own]),
            "own_confirmed_plants": dict(plants[own]), "rival_confirmed_plants": dict(plants[1 - own]),
            "own_confirmed_places": dict(places[own]), "rival_confirmed_places": dict(places[1 - own]),
            "snapshots": snapshots}


def main() -> None:
    results = {name: summarize(HERE / f"loss_trace_{name}_s0.json.gz") for name in NAMES}
    out = HERE / "current_loss_cash_audit.json"
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    for name, row in results.items():
        print(name, "margin", row["margin"])
        print("  sales own", row["own_sale_cash"])
        print("  sales rival", row["rival_sale_cash"])
        print("  costs own", row["own_cash_cost"])
        print("  plants own/rival", row["own_confirmed_plants"], row["rival_confirmed_plants"])
        for snap in row["snapshots"]:
            if snap["day"] in (6, 12, 18, 24, 29):
                print("  day", snap["day"], "cash", snap["own_cash"], snap["rival_cash"],
                      "tiles", snap["own_tiles"], snap["rival_tiles"])
    print("wrote", out)


if __name__ == "__main__":
    main()
