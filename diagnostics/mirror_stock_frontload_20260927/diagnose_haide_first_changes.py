"""Trace only the first causal action difference in changed Haide A/B seeds."""

import gc
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from trace_paired_game import run  # noqa: E402


HERE = Path(__file__).resolve().parent
BASE = ROOT / "main.py"
CANDIDATE = ROOT / "exp_mirror_stock_frontload_halfbase_20260927.py"
OPPONENT = (ROOT / "kaggle_complete_agents_live_2026-09-23_page6_top100"
            / "093-haideptry__countering-the-big-3-meta__b6eec8c43ecb.py")
BASE_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
CANDIDATE_HASH = "e9517daebe5523879c5096839570af04619135fc7f5a7fb7e6446ab1c367ca68"
SEEDS = (2614351, 2614352, 2614353, 2614355)
SEAT = 0


def summarize(seed, reported):
    control = run(str(BASE), str(OPPONENT), seed, SEAT)
    trial = run(str(CANDIDATE), str(OPPONENT), seed, SEAT)
    expected = {(row["arm"], row["seed"], row["candidate_seat"]): row
                for row in reported["rows"]}
    for arm, game in (("control", control), ("treatment", trial)):
        official = expected[arm, seed, SEAT]
        assert (game["candidate_reward"], game["opponent_reward"]) == (official["candidate_reward"], official["opponent_reward"])
    base_trace = control["traces"][SEAT]
    trial_trace = trial["traces"][SEAT]
    first = next((i for i, (a, b) in enumerate(zip(base_trace, trial_trace))
                  if a["action"] != b["action"]), None)
    if first is None:
        return {"seed": seed, "first_difference": None}
    record = trial_trace[first]
    obs = record["observation"]
    pre = trial_trace[max(0, first - 4):first + 1]
    def upcoming_sales(trace):
        found = []
        for row in trace[first:min(len(trace), first + 40)]:
            orders = [order for order in (row["action"].get("market") or [])
                      if isinstance(order, list) and len(order) > 2
                      and order[0] == "SELL" and order[1] == "STRAWBERRY"]
            if orders:
                found.append({"step": row["step"],
                              "quote": row["observation"].get("market", {}).get("prices", {}).get("STRAWBERRY"),
                              "orders": orders})
            if len(found) >= 5:
                break
        return found
    def previous_sales(trace):
        found = []
        for row in trace[max(0, first - 120):first]:
            orders = [order for order in (row["action"].get("market") or [])
                      if isinstance(order, list) and len(order) > 2
                      and order[0] == "SELL" and order[1] == "STRAWBERRY"]
            if orders:
                found.append({"step": row["step"],
                              "quote": row["observation"].get("market", {}).get("prices", {}).get("STRAWBERRY"),
                              "orders": orders})
        return found[-5:]
    result = {
        "seed": seed, "first_difference": record["step"],
        "control_margin": control["margin"], "trial_margin": trial["margin"],
        "control_own": control["candidate_reward"], "trial_own": trial["candidate_reward"],
        "control_rival": control["opponent_reward"], "trial_rival": trial["opponent_reward"],
        "stock": int(obs.get("private", {}).get("shed", {}).get("STRAWBERRY", 0) or 0),
        "quote_history": [
            {"step": row["step"],
             "quote": row["observation"].get("market", {}).get("prices", {}).get("STRAWBERRY"),
             "stock": row["observation"].get("private", {}).get("shed", {}).get("STRAWBERRY")}
            for row in pre],
        "market_inventory": obs.get("market", {}).get("inventory", {}).get("STRAWBERRY"),
        "control_action": base_trace[first]["action"],
        "trial_action": record["action"],
        "rival_action_same_turn": trial["traces"][1 - SEAT][first]["action"],
        "baseline_next_strawberry_sales": upcoming_sales(base_trace),
        "trial_next_strawberry_sales": upcoming_sales(trial_trace),
        "haide_next_strawberry_sales": upcoming_sales(trial["traces"][1 - SEAT]),
        "baseline_previous_strawberry_sales": previous_sales(base_trace),
        "haide_previous_strawberry_sales": previous_sales(trial["traces"][1 - SEAT]),
    }
    del control, trial, base_trace, trial_trace
    gc.collect()
    return result


def main():
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_HASH
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == CANDIDATE_HASH
    reported = json.loads((HERE / "reactive_haide_halfbase.json").read_text(encoding="utf-8"))
    rows = []
    for seed in SEEDS:
        row = summarize(seed, reported)
        rows.append(row)
        print(seed, "first", row["first_difference"],
              "quotes", row.get("quote_history"),
              "own_delta", row.get("trial_own", 0) - row.get("control_own", 0),
              "margin_delta", row.get("trial_margin", 0) - row.get("control_margin", 0),
              flush=True)
    output = HERE / "haide_first_changes.json"
    output.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
