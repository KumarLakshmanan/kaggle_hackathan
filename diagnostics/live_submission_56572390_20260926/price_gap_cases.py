"""Explain matched-turn versus timing components in selected sale gaps."""

from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from trace_paired_game_events import run  # noqa: E402


SOURCE = ROOT / "main.py"
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
EPISODES = (113642505, 113662620, 113667319, 113634238)
ITEMS = ("STRAWBERRY", "WOOL")


def play(job):
    live, route = job
    seat = int(live["our_seat"])
    data = run(str(SOURCE), f"rawroute:{route['path']}", int(live["seed"]), seat)
    assert data["candidate_status"] == data["opponent_status"] == "DONE"
    assert (data["candidate_reward"], data["opponent_reward"]) == (live["our_cash"], live["rival_cash"])
    sales = defaultdict(lambda: [0.0, 0])
    for event in data["events"]:
        if (event.get("phase") == "market_unit" and event.get("success")
                and event.get("operation") == "SELL" and event.get("item") in ITEMS
                and int(event.get("step", -1)) >= 480):
            slot = sales[(event["item"], int(event["step"]), int(event["player"]))]
            slot[0] += float(event["cash_delta"])
            slot[1] += 1
    by_item = {}
    for item in ITEMS:
        steps = sorted({step for product, step, _ in sales if product == item})
        matched_cash_gap = 0.0
        mismatched_cash_gap = 0.0
        matched_turns = 0
        mismatched_turns = 0
        own_total = rival_total = own_units = rival_units = 0
        for step in steps:
            own_cash, our_n = sales[(item, step, seat)]
            rival_cash, their_n = sales[(item, step, 1 - seat)]
            own_total += own_cash
            rival_total += rival_cash
            own_units += our_n
            rival_units += their_n
            if our_n > 0 and our_n == their_n:
                matched_cash_gap += own_cash - rival_cash
                matched_turns += 1
            else:
                mismatched_cash_gap += own_cash - rival_cash
                mismatched_turns += 1
        by_item[item] = {"own_sale_cash": own_total, "rival_sale_cash": rival_total,
                         "sale_cash_gap": own_total - rival_total,
                         "own_units": own_units, "rival_units": rival_units,
                         "matched_unit_turns": matched_turns,
                         "matched_unit_turns_cash_gap": matched_cash_gap,
                         "different_unit_turns": mismatched_turns,
                         "different_unit_turns_cash_gap": mismatched_cash_gap}
    return {"episode_id": live["episode_id"], "opponent": live["opponent"],
            "margin": live["margin"], "our_seat": seat, "items": by_item}


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    lives = {row["episode_id"]: row for row in json.loads((HERE / "audit_latest_100.json").read_text(encoding="utf-8"))["episodes"]}
    routes = {row["episode_id"]: row for row in json.loads((HERE / "mirror_dev_routes" / "summary.json").read_text(encoding="utf-8"))}
    with ProcessPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(play, [(lives[episode], routes[episode]) for episode in EPISODES]))
    summary = {
        item: {
            key: sum(row["items"][item][key] for row in rows)
            for key in ("sale_cash_gap", "own_units", "rival_units", "matched_unit_turns",
                        "matched_unit_turns_cash_gap", "different_unit_turns",
                        "different_unit_turns_cash_gap")
        }
        for item in ITEMS
    }
    output = {"source_sha256": EXPECTED, "summary": summary, "rows": rows}
    destination = HERE / f"price_gap_cases_{len(EPISODES)}.json"
    destination.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(destination)


if __name__ == "__main__":
    main()
