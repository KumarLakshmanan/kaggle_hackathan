from pathlib import Path
from collections import Counter
import json
import tempfile
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

PROJECT_DIR = Path.cwd()
if not (PROJECT_DIR / "replays").exists() and (PROJECT_DIR / "kaggriculture" / "replays").exists():
    PROJECT_DIR = PROJECT_DIR / "kaggriculture"

REPLAY_FILES = sorted((PROJECT_DIR / "replays" / "ladder").glob("*.json"))
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
SEED_COSTS = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}

def create_demo_replay():
    # Create a small synthetic replay when no external JSON is available.
    steps = []
    for day in range(30):
        farms = [
            {"money": 3000 + day * 1000, "tiles": [], "farmer": [4, 4], "hands": []},
            {"money": 3000 + day * 1300, "tiles": [], "farmer": [4, 4], "hands": []},
        ]
        records = []
        for player in range(2):
            product = "MELON" if player == 0 else "MILK"
            quantity = 3 + player * 2
            records.append({
                "observation": {
                    "day": day, "hour": 23, "player": player, "farms": farms,
                    "private": {"inventories": [], "seeds": {}, "shed": {}},
                    "market": {"prices": {item: 100 for item in PRODUCTS}},
                },
                "action": {
                    "farmer": ["PASS"] if day % (5 - player) == 0 else ["HARVEST"],
                    "hands": [], "market": [["SELL", product, quantity]],
                },
            })
        steps.append(records)
    return {"id": "synthetic-demo", "info": {"Agents": [{"Name": "Baseline"}, {"Name": "Improved agent"}]}, "steps": steps}

if not REPLAY_FILES:
    demo_path = Path(tempfile.gettempdir()) / "kaggriculture_replay_lab_demo.json"
    demo_path.write_text(json.dumps(create_demo_replay()), encoding="utf-8")
    REPLAY_FILES = [demo_path]
    print("No external replay found: using the built-in synthetic replay.")
else:
    print(f"{len(REPLAY_FILES)} replay(s) found")

def analyse_replay(path):
    replay = json.loads(path.read_text(encoding="utf-8-sig"))
    steps = replay.get("steps") or []
    if not steps or not isinstance(steps[0], list):
        raise ValueError(f"Invalid replay: {path.name}")
    agents = (replay.get("info") or {}).get("Agents") or []
    players = []
    for p in range(len(steps[0])):
        name = agents[p].get("Name") if p < len(agents) and isinstance(agents[p], dict) else None
        unit_ops, market_qty, money_by_day = Counter(), Counter(), {}
        for step in steps:
            record = step[p] or {}; obs = record.get("observation") or {}; action = record.get("action") or {}
            farms = obs.get("farms") or []; farm = farms[p] if p < len(farms) else {}
            money_by_day[int(obs.get("day", 0) or 0)] = float(farm.get("money", 0) or 0)
            for command in [action.get("farmer", ["PASS"]), *(action.get("hands") or [])]:
                unit_ops[command[0] if command else "EMPTY"] += 1
            for order in action.get("market") or []:
                if order and len(order) >= 3 and isinstance(order[2], (int, float)):
                    market_qty[(order[0], order[1])] += int(order[2])
        last = steps[-1][p].get("observation") or {}; farms = last.get("farms") or []
        farm = farms[p] if p < len(farms) else {}; private = last.get("private") or {}
        prices = ((last.get("market") or {}).get("prices") or {})
        unharvested, weeds = Counter(), 0
        for row in farm.get("tiles") or []:
            for tile in row:
                if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                    unharvested[tile.get("crop", "UNKNOWN")] += int(tile.get("yield_units", 0) or 0)
                elif isinstance(tile, dict) and tile.get("kind") == "WEED": weeds += 1
        carried = Counter()
        for inventory in private.get("inventories") or []: carried.update(inventory or {})
        seeds, shed = private.get("seeds") or {}, private.get("shed") or {}
        end_value = (sum(int(q or 0)*SEED_COSTS.get(k,0) for k,q in seeds.items())
                     + sum(int(q or 0)*int(prices.get(k,0) or 0) for k,q in unharvested.items())
                     + sum(int(q or 0)*int(prices.get(k,0) or 0) for k,q in carried.items())
                     + sum(int(q or 0)*int(prices.get(k,0) or 0) for k,q in shed.items()))
        total_actions = sum(unit_ops.values())
        players.append({"player":p,"agent":name or f"Joueur {p}","final_money":float(farm.get("money",0) or 0),
                        "money_by_day":money_by_day,"unit_ops":dict(unit_ops),"market_qty":dict(market_qty),
                        "pass_rate":unit_ops.get("PASS",0)/total_actions if total_actions else 0,
                        "end_value":end_value,"weeds":weeds})
    return {"episode":replay.get("id") or path.stem,"file":path.name,"players":players,"steps":len(steps)}

analyses = [analyse_replay(path) for path in REPLAY_FILES]
assert analyses, "Add at least one replay JSON to replays/ladder."
print("Analysis completed successfully.")

summary_rows = []
for match in analyses:
    ranked = sorted(match["players"], key=lambda x: x["final_money"], reverse=True)
    summary_rows.append({"Replay":match["file"], "Winner":ranked[0]["agent"],
                         "Winning score":ranked[0]["final_money"],
                         "Margin":ranked[0]["final_money"]-ranked[1]["final_money"],
                         "Winner unbanked value":ranked[0]["end_value"]})
summary = pd.DataFrame(summary_rows)
display(summary.style.format({"Winning score":"{:,.0f}","Margin":"{:+,.0f}","Winner unbanked value":"{:,.0f}"}))

example = analyses[0]
fig, ax = plt.subplots(figsize=(10, 4.5))
for player in example["players"]:
    series = pd.Series(player["money_by_day"]).sort_index()
    ax.plot(series.index, series.values, marker="o", markersize=3, label=player["agent"])
ax.set(title=f"Economic trajectory — {example['file']}", xlabel="Day", ylabel="Cash")
ax.legend(); ax.grid(alpha=.25); plt.tight_layout(); plt.show()

sales_rows = []
for player in example["players"]:
    for product in PRODUCTS:
        sales_rows.append({"Product":product.title(),"Quantity":player["market_qty"].get(("SELL",product),0),"Agent":player["agent"]})
sales = pd.DataFrame(sales_rows)
pivot = sales.pivot(index="Product", columns="Agent", values="Quantity").fillna(0)
display(pivot)
pivot.plot(kind="bar", figsize=(11,4.5), rot=35, title="Sales volume by product")
plt.ylabel("Units sold"); plt.tight_layout(); plt.show()

efficiency = pd.DataFrame([
    {"Replay":m["file"],"Agent":p["agent"],"Final score":p["final_money"],
     "PASS":p["pass_rate"],"Unbanked value":p["end_value"],"Final weeds":p["weeds"]}
    for m in analyses for p in m["players"]
])
display(efficiency.style.format({"Final score":"{:,.0f}","PASS":"{:.1%}","Unbanked value":"{:,.0f}"}))
assert efficiency["PASS"].between(0,1).all()
assert (efficiency[["Final score","Unbanked value","Final weeds"]] >= 0).all().all()
print("Consistency checks passed.")