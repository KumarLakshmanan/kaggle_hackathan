"""Read-only final-state inventory check for the frozen 29 public losses."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
episodes = json.loads((ROOT / "audit_latest_100.json").read_text(encoding="utf-8"))["episodes"]
rows = []
for episode in episodes:
    if episode["margin"] >= 0:
        continue
    replay = json.loads((ROOT / f"episode-{episode['episode_id']}-replay.json").read_text(encoding="utf-8"))
    final = replay["steps"][-1][episode["our_seat"]]
    observation = final["observation"]
    private = observation["private"]
    shed = {name: int(count) for name, count in private["shed"].items() if count}
    carried = [dict(inventory) for inventory in private.get("inventories", []) if inventory]
    prices = observation["market"]["prices"]
    gross_quote = sum(prices.get(name, 0) * count for name, count in shed.items())
    gross_quote += sum(prices.get(name, 0) * count for inventory in carried for name, count in inventory.items())
    rows.append({
        "episode_id": episode["episode_id"],
        "opponent": episode["opponent"],
        "margin": episode["margin"],
        "our_seat": episode["our_seat"],
        "terminal_shed": shed,
        "terminal_carried": carried,
        "terminal_gross_quote": gross_quote,
        "last_market_action": final["action"]["market"],
    })
output = {"submission": 56572390, "losses": len(rows), "positive_terminal_inventory": sum(row["terminal_gross_quote"] > 0 for row in rows), "total_terminal_quote": sum(row["terminal_gross_quote"] for row in rows), "rows": rows}
(ROOT / "terminal_inventory_losses.json").write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({key: value for key, value in output.items() if key != "rows"}, indent=2))
for row in rows:
    if row["terminal_gross_quote"] > 0:
        print(row["opponent"], row["margin"], row["terminal_gross_quote"], row["terminal_shed"], row["terminal_carried"])
