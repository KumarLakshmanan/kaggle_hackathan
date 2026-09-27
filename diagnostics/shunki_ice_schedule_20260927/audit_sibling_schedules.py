"""Static search for compatible source tapes with missing scheduled planting.

This reads action data only. A score here is a diagnostic, not profitability
or a promotion rule: surplus seeds and legitimate changes of plans exist.
"""
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCES = ROOT / "diagnostics/shunki_portfolio_20260927"
COSTS = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}


def main():
    manifest = json.loads((SOURCES / "route_manifest.json").read_text(encoding="utf8"))
    mapping = json.loads((SOURCES / "later_shop_analysis.json").read_text(encoding="utf8"))["route_map"]
    by_pair = defaultdict(list)
    routes = {}
    for source in manifest["rows"]:
        with gzip.open(source["route_path"], "rt", encoding="utf8") as handle:
            actions = json.load(handle)["actions"]
        bought, planted, animal_buys, places = Counter(), Counter(), Counter(), Counter()
        for action in actions:
            for order in action.get("market", []):
                if len(order) >= 3 and order[0] == "BUY_SEED":
                    bought[order[1]] += order[2]
                elif len(order) >= 3 and order[0] == "BUY_ANIMAL":
                    animal_buys[order[1]] += order[2]
            for unit in [action.get("farmer", [])] + action.get("hands", []):
                if len(unit) >= 2 and unit[0] == "PLANT":
                    planted[unit[1]] += 1
                elif len(unit) >= 2 and unit[0] == "PLACE" and unit[1] in ("GOOSE", "COW", "SHEEP"):
                    places[unit[1]] += 1
        row = {"episode_id": source["episode_id"], "shops": source["shops_day6"],
               "seed_buys": dict(bought), "plant_commands": dict(planted),
               "animal_buys": dict(animal_buys), "place_commands": dict(places),
               "unplanted_seed_value": sum(COSTS.get(item, 0) * max(0, qty - planted[item]) for item, qty in bought.items())}
        routes[source["episode_id"]] = (actions, row)
        by_pair[tuple(source["shops_day6"])].append(source["episode_id"])
    alternatives = []
    for pair, episodes in by_pair.items():
        current_id = mapping["|".join(pair)]
        current, current_summary = routes[current_id]
        for other_id in episodes:
            if other_id == current_id:
                continue
            other, other_summary = routes[other_id]
            common = next((i for i, (a, b) in enumerate(zip(current, other)) if a != b), 719)
            if common < 144:
                continue
            gap = current_summary["unplanted_seed_value"] - other_summary["unplanted_seed_value"]
            if gap > 0:
                alternatives.append({"shops": pair, "current": current_summary, "alternative": other_summary,
                                     "exact_common_prefix": common, "unplanted_value_gap": gap,
                                     "same_total_seed_buys": current_summary["seed_buys"] == other_summary["seed_buys"]})
    alternatives.sort(key=lambda r: -r["unplanted_value_gap"])
    (HERE / "sibling_schedule_audit.json").write_text(json.dumps({"alternatives": alternatives,
                                                                  "routes": [row for _, row in routes.values()]}, indent=2), encoding="utf8")
    for row in alternatives[:12]:
        print(row["shops"], row["current"]["episode_id"], "->", row["alternative"]["episode_id"],
              "common", row["exact_common_prefix"], "gap", row["unplanted_value_gap"], "same buys", row["same_total_seed_buys"])


if __name__ == "__main__":
    main()
