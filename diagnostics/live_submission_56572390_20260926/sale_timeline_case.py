"""Executed strawberry-sale timeline on one original live loss."""

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from trace_paired_game_events import run  # noqa: E402


EPISODE = 113642505
SOURCE = ROOT / "main.py"
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    audit = json.loads((HERE / "audit_latest_100.json").read_text(encoding="utf-8"))["episodes"]
    routes = json.loads((HERE / "mirror_dev_routes" / "summary.json").read_text(encoding="utf-8"))
    live = next(row for row in audit if row["episode_id"] == EPISODE)
    route = next(row for row in routes if row["episode_id"] == EPISODE)
    seat = int(live["our_seat"])
    data = run(str(SOURCE), f"rawroute:{route['path']}", int(live["seed"]), seat)
    assert (data["candidate_reward"], data["opponent_reward"]) == (live["our_cash"], live["rival_cash"])
    by_step = defaultdict(lambda: [[0, 0.0], [0, 0.0]])
    for event in data["events"]:
        if (event.get("phase") == "market_unit" and event.get("operation") == "SELL"
                and event.get("item") == "STRAWBERRY" and event.get("success")):
            own_or_rival = 0 if int(event["player"]) == seat else 1
            bucket = by_step[int(event["step"])][own_or_rival]
            bucket[0] += 1
            bucket[1] += float(event["cash_delta"])
    inventories = {int(turn["step"]): int(turn["market_before"]["inventory"]["STRAWBERRY"])
                   for turn in data["turns"] if "inventory" in turn["market_before"]}
    rows = []
    for step in sorted(by_step):
        own, rival = by_step[step]
        rows.append({"step": step, "day": step // 24,
                     "inventory_before": inventories.get(step),
                     "our_units": own[0], "rival_units": rival[0],
                     "our_cash": own[1], "rival_cash": rival[1],
                     "receipt_gap": own[1] - rival[1]})
    output = {"episode_id": EPISODE, "team": live["opponent"],
              "margin": live["margin"], "our_seat": seat,
              "total_strawberry_gap": sum(row["receipt_gap"] for row in rows),
              "rows": rows}
    destination = HERE / "sale_timeline_113642505.json"
    destination.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print("gap", output["total_strawberry_gap"], "turns", len(rows))
    for row in sorted(rows, key=lambda row: row["receipt_gap"])[:18]:
        print(row)
    print(destination)


if __name__ == "__main__":
    main()
