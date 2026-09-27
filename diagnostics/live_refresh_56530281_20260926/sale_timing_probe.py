"""Inspect exact executed unit-sale price differences on a public live episode."""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from trace_paired_game_events import run  # noqa: E402


def main() -> None:
    episode = int(sys.argv[1])
    item = sys.argv[2] if len(sys.argv) > 2 else "STRAWBERRY"
    source = next(r for r in json.loads((HERE / "summary.json").read_text(encoding="utf8"))
                  if int(r["episode_id"]) == episode)
    live = next(r for r in json.loads((HERE / "audit_latest_40.json").read_text(encoding="utf8"))["episodes"]
                if int(r["episode_id"]) == episode)
    seat = int(live["our_seat"])
    data = run(
        candidate=str(ROOT / "main_before_top10_goal_20260926_04b0bdc3.py"),
        opponent=f"rawroute:{source['path']}",
        seed=int(source["seed"]), candidate_seat=seat,
    )
    assert (data["candidate_reward"], data["opponent_reward"]) == (
        live["our_cash"], live["rival_cash"]
    )
    by_step: dict[int, dict[int, dict]] = defaultdict(lambda: defaultdict(
        lambda: {"units": 0, "cash": 0.0, "prices": []}))
    for event in data["events"]:
        if (event.get("phase") == "market_unit" and event.get("success")
                and event.get("operation") == "SELL" and event.get("item") == item):
            slot = by_step[int(event["step"])][int(event["player"])]
            slot["units"] += 1
            slot["cash"] += float(event["cash_delta"])
            slot["prices"].append(float(event["quoted_unit_price"]))
    out = []
    for step in sorted(by_step):
        a = by_step[step][seat]
        b = by_step[step][1 - seat]
        if a["units"] == b["units"] and a["cash"] == b["cash"]:
            continue
        trace_ours = data["traces"][seat]
        trace_rival = data["traces"][1 - seat]
        own_action = next((t.get("action", {}) for t in trace_ours
                           if int(t["step"]) == step), {})
        rival_action = next((t.get("action", {}) for t in trace_rival
                             if int(t["step"]) == step), {})
        row = {
            "step": step, "day": step // 24,
            "own_units": a["units"], "rival_units": b["units"],
            "own_cash": a["cash"], "rival_cash": b["cash"],
            "cash_difference": a["cash"] - b["cash"],
            "own_price_range": [min(a["prices"]), max(a["prices"])] if a["prices"] else [],
            "rival_price_range": [min(b["prices"]), max(b["prices"])] if b["prices"] else [],
            "own_market_action": own_action.get("market", []),
            "rival_market_action": rival_action.get("market", []),
        }
        out.append(row)
    dest = HERE / f"sale_probe_{episode}_{item.lower()}.json"
    dest.write_text(json.dumps({"episode": episode, "item": item,
                                "own_seat": seat, "rows": out},
                               indent=2, ensure_ascii=False), encoding="utf8")
    print("episode", episode, "item", item, "turns", len(out),
          "difference", sum(r["cash_difference"] for r in out))
    for row in sorted(out, key=lambda r: abs(r["cash_difference"]), reverse=True)[:12]:
        print(row["step"], row["cash_difference"],
              row["own_units"], row["rival_units"],
              "own", row["own_market_action"],
              "rival", row["rival_market_action"])
    print(dest)


if __name__ == "__main__":
    main()
