"""Observed quote distribution for late requested premium-product sales."""

import json
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parent
episodes = json.loads((ROOT / "audit_latest_100.json").read_text(encoding="utf-8"))["episodes"]
products = ("STRAWBERRY", "WOOL", "MILK", "CARROT")
quotes = {name: [] for name in products}
requests = {name: 0 for name in products}
low_requests = {name: 0 for name in products}
thresholds = {"STRAWBERRY": 60, "WOOL": 100, "MILK": 80, "CARROT": 30}
for episode in episodes:
    if episode["outcome"] != "loss":
        continue
    replay = json.loads((ROOT / f"episode-{episode['episode_id']}-replay.json").read_text(encoding="utf-8"))
    seat = int(episode["our_seat"])
    for frame_index in range(481, len(replay["steps"])):
        before = replay["steps"][frame_index - 1][seat]["observation"]
        orders = replay["steps"][frame_index][seat].get("action", {}).get("market", []) or []
        for order in orders:
            if len(order) < 3 or order[0] != "SELL" or order[1] not in products:
                continue
            item = order[1]
            quote = int(before["market"]["prices"][item])
            quantity = int(order[2])
            quotes[item].append(quote)
            requests[item] += quantity
            if quote < thresholds[item]:
                low_requests[item] += quantity
output = {item: {"sale_request_turns": len(quotes[item]), "requested_units": requests[item],
                 "quote_min": min(quotes[item]) if quotes[item] else None,
                 "quote_median": median(quotes[item]) if quotes[item] else None,
                 "quote_max": max(quotes[item]) if quotes[item] else None,
                 "threshold": thresholds[item], "requested_units_below_threshold": low_requests[item]}
          for item in products}
(ROOT / "late_quote_exposure.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
print(json.dumps(output, indent=2))
