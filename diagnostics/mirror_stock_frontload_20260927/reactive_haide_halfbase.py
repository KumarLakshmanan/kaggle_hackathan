"""Matched native A/B against one reacting public near-clone opponent."""

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402


BASE = ROOT / "main.py"
CANDIDATE = ROOT / "exp_mirror_stock_frontload_halfbase_20260927.py"
OPPONENT = (ROOT / "kaggle_complete_agents_live_2026-09-23_page6_top100"
            / "093-haideptry__countering-the-big-3-meta__b6eec8c43ecb.py")
BASE_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
CANDIDATE_HASH = "e9517daebe5523879c5096839570af04619135fc7f5a7fb7e6446ab1c367ca68"
OPPONENT_HASH = "4f3ca95dd12d9a94b03339999d8803c155f450a8d3956636f050643301fcc5dd"
SEEDS = tuple(range(2614350, 2614358))
OUTPUT = Path(__file__).with_name("reactive_haide_halfbase.json")


def play(job):
    arm, seed, seat = job
    source = BASE if arm == "control" else CANDIDATE
    row = run_game(str(source), str(OPPONENT), seed, seat, False, None, {})
    row["arm"] = arm
    return row


def main():
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_HASH
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == CANDIDATE_HASH
    assert hashlib.sha256(OPPONENT.read_bytes()).hexdigest() == OPPONENT_HASH
    jobs = [(arm, seed, seat) for arm in ("control", "treatment")
            for seed in SEEDS for seat in (0, 1)]
    rows = []
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(play, job): job for job in jobs}
        for completed in as_completed(futures):
            row = completed.result()
            rows.append(row)
            print(row["arm"], row["seed"], row["candidate_seat"],
                  "margin", row["margin"], "trigger",
                  (row.get("candidate_telemetry") or {}).get("latch_trigger_turns"),
                  "status", row["candidate_status"], row["opponent_status"], flush=True)
    rows.sort(key=lambda row: (row["arm"], row["seed"], row["candidate_seat"]))
    by_key = {(row["arm"], row["seed"], row["candidate_seat"]): row for row in rows}
    comparisons = []
    for seed in SEEDS:
        for seat in (0, 1):
            base = by_key["control", seed, seat]
            trial = by_key["treatment", seed, seat]
            comparisons.append({
                "seed": seed, "seat": seat,
                "baseline_margin": base["margin"], "candidate_margin": trial["margin"],
                "margin_delta": trial["margin"] - base["margin"],
                "own_cash_delta": trial["candidate_reward"] - base["candidate_reward"],
                "rival_cash_delta": trial["opponent_reward"] - base["opponent_reward"],
                "trigger_turns": (trial.get("candidate_telemetry") or {}).get("latch_trigger_turns", 0),
            })
    pair_delta = {seed: sum(row["margin_delta"] for row in comparisons if row["seed"] == seed)
                  for seed in SEEDS}
    treatment = [row for row in rows if row["arm"] == "treatment"]
    summary = {
        "trigger_games": sum(row["trigger_turns"] > 0 for row in comparisons),
        "positive_pair_deltas": sum(value > 0 for value in pair_delta.values()),
        "negative_pair_deltas": sum(value < 0 for value in pair_delta.values()),
        "tied_pair_deltas": sum(value == 0 for value in pair_delta.values()),
        "own_cash_delta": sum(row["own_cash_delta"] for row in comparisons),
        "rival_cash_delta": sum(row["rival_cash_delta"] for row in comparisons),
        "margin_delta": sum(row["margin_delta"] for row in comparisons),
        "baseline_wins": sum(row["baseline_margin"] > 0 for row in comparisons),
        "candidate_wins": sum(row["candidate_margin"] > 0 for row in comparisons),
        "win_reversals": sum(row["baseline_margin"] > 0 >= row["candidate_margin"]
                             for row in comparisons),
        "all_done": all(row["candidate_status"] == row["opponent_status"] == "DONE"
                        for row in rows),
        "error_games": sum(any(key.endswith("errors") and value
                               for key, value in (row.get("candidate_telemetry") or {}).items())
                           for row in treatment),
        "max_call_ms": max(row["candidate_timing"]["max_ms"] for row in treatment),
    }
    summary["diagnostic_gate_passed"] = (
        summary["trigger_games"] >= 8 and summary["positive_pair_deltas"] >= 5
        and summary["own_cash_delta"] > 0 and summary["margin_delta"] > 0
        and summary["win_reversals"] == 0 and summary["all_done"]
        and summary["error_games"] == 0)
    OUTPUT.write_text(json.dumps({"source_hashes": {"base": BASE_HASH,
                              "candidate": CANDIDATE_HASH, "opponent": OPPONENT_HASH},
                              "seeds": SEEDS, "summary": summary,
                              "paired_seed_deltas": pair_delta,
                              "comparisons": comparisons, "rows": rows}, indent=2),
                      encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(OUTPUT)


if __name__ == "__main__":
    main()
