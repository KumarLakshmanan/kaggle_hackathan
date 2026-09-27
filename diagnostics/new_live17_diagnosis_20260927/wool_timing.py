"""Exact executed WOOL cash and public quotes in the Takahiro loss."""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from trace_paired_game_events import run  # noqa: E402

EPISODE = 113800419


def main() -> None:
    routes = json.loads((HERE / "routes" / "summary.json").read_text(encoding="utf8"))
    route = next(row for row in routes if row["episode_id"] == EPISODE)
    seat = int(route["our_seat"])
    data = run(str(ROOT / "main.py"), f"rawroute:{route['path']}", int(route["seed"]), seat)
    assert (data["candidate_reward"], data["opponent_reward"]) == (
        route["our_live_cash"], route["rival_live_cash"])
    replay_dir = HERE.parent / "physical_sale_predictor_20260927"
    replay = json.loads((replay_dir / f"episode-{EPISODE}-replay.json").read_text(encoding="utf8"))
    by_turn = defaultdict(lambda: [0.0, 0, 0.0, 0])
    for event in data["events"]:
        if (event.get("success") and event.get("phase") == "market_unit"
                and event.get("operation") == "SELL" and event.get("item") == "WOOL"
                and event.get("player") in (0, 1)):
            turn = int(event["step"])
            slot = by_turn[turn]
            index = 0 if int(event["player"]) == seat else 2
            slot[index] += float(event["cash_delta"])
            slot[index+1] += 1
    turns = []
    for turn in sorted(by_turn):
        own_cash, own_units, rival_cash, rival_units = by_turn[turn]
        obs = replay["steps"][turn][seat]["observation"]
        assert int(obs.get("step", turn)) == turn
        own_action = replay["steps"][turn+1][seat].get("action") or {}
        rival_action = replay["steps"][turn+1][1-seat].get("action") or {}
        own_request = sum(int(o[2]) for o in own_action.get("market") or []
                          if isinstance(o, list) and len(o) >= 3 and o[:2] == ["SELL", "WOOL"])
        rival_request = sum(int(o[2]) for o in rival_action.get("market") or []
                            if isinstance(o, list) and len(o) >= 3 and o[:2] == ["SELL", "WOOL"])
        turns.append({"turn": turn, "day": turn//24, "hour": turn%24,
                      "quote_before": obs["market"]["prices"]["WOOL"],
                      "inventory_before": obs["market"]["inventory"]["WOOL"],
                      "own_shed_before": obs["private"]["shed"].get("WOOL", 0),
                      "own_requested": own_request, "rival_requested": rival_request,
                      "own_units": own_units, "rival_units": rival_units,
                      "own_cash": own_cash, "rival_cash": rival_cash,
                      "cash_gap": own_cash-rival_cash})
    daily = []
    for day in range(30):
        sub = [row for row in turns if row["day"] == day]
        daily.append({"day": day, "own_units": sum(row["own_units"] for row in sub),
                      "rival_units": sum(row["rival_units"] for row in sub),
                      "own_cash": sum(row["own_cash"] for row in sub),
                      "rival_cash": sum(row["rival_cash"] for row in sub),
                      "cash_gap": sum(row["cash_gap"] for row in sub),
                      "first_own_turn": min((row["turn"] for row in sub if row["own_units"]), default=None),
                      "first_rival_turn": min((row["turn"] for row in sub if row["rival_units"]), default=None)})
    summary = {"episode_id": EPISODE, "our_seat": seat,
               "total_own_units": sum(row["own_units"] for row in turns),
               "total_rival_units": sum(row["rival_units"] for row in turns),
               "total_own_cash": sum(row["own_cash"] for row in turns),
               "total_rival_cash": sum(row["rival_cash"] for row in turns),
               "largest_negative_days": sorted(daily, key=lambda row: row["cash_gap"])[:8]}
    output = {"summary": summary, "daily": daily, "turns": turns}
    (HERE / "takahiro_wool_timeline.json").write_text(json.dumps(output, indent=2), encoding="utf8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
