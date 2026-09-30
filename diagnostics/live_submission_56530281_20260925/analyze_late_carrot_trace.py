"""Read-only exact receipt/plant comparison for the late-carrot target trace."""

from collections import Counter
import gzip
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
TRACE_FILES = {
    "baseline": HERE / "late_carrot_trace_baseline_113151063.json.gz",
    "candidate": HERE / "late_carrot_trace_candidate_113151063.json.gz",
}

for label, path in TRACE_FILES.items():
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        data = json.load(stream)
    player = int(data["candidate_seat"])
    market = Counter()
    plants = Counter()
    for event in data["events"]:
        if int(event.get("player", -1)) != player or int(event.get("step", -1)) < 652:
            continue
        if event["phase"] == "unit_action" and event.get("action", [])[:1] == ["PLANT"]:
            item = event["action"][1] if len(event["action"]) > 1 else "?"
            plants[f"{item}_requested"] += 1
            plants[f"{item}_changed"] += int(bool(event.get("changed")))
        if event["phase"] == "market_unit" and event.get("item") in ("CARROT", "WHEAT"):
            key = f"{event['operation']}_{event['item']}"
            market[f"{key}_requested"] += 1
            if event.get("success"):
                market[f"{key}_executed"] += 1
                market[f"{key}_cash"] += int(event.get("cash_delta", 0))
    final = data["traces"][player][-1]["observation"]
    start = data["traces"][player][652]["observation"]
    print(label, "own/rival", data["candidate_reward"], data["opponent_reward"],
          "late start cash", start["farms"][player]["money"],
          "final shed", {k: v for k, v in final["private"]["shed"].items() if v},
          "final seeds", {k: v for k, v in final["private"]["seeds"].items() if v})
    print("  late plants", dict(plants))
    print("  late carrot/wheat market", dict(market))
    print("  shops", final["town"]["unlocked_shops"])
