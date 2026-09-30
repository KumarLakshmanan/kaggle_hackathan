"""Matched public-agent reactive checks of mirror lookahead 12 versus 8."""

from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

BASE = ROOT / "main.py"
CANDIDATE = ROOT / "exp_sale_mirror12_20260926.py"
OPPONENTS = {
    "public_h6": ROOT / "kaggle_complete_agents_live_2026-09-22_current_page4_top100"
    / "019-koushikrudra__kaggriculture-preempt-h6__9193c450d5d5.py",
    "haide": ROOT / "kaggle_complete_agents_live_2026-09-23_page6_top100"
    / "093-haideptry__countering-the-big-3-meta__b6eec8c43ecb.py",
}
SEEDS = tuple(range(2610320, 2610324))
OUTPUT = Path(__file__).with_name("reactive_mirror12_public.json")


def play(job):
    name, arm, seed, seat = job
    row = run_game(str(BASE if arm == "control" else CANDIDATE),
                   str(OPPONENTS[name]), seed, seat, False, None, {})
    row["opponent_name"] = name
    row["arm"] = arm
    return row


def main():
    jobs = [(name, arm, seed, seat)
            for name in OPPONENTS
            for arm in ("control", "treatment")
            for seed in SEEDS for seat in (0, 1)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    assert len(rows) == 32
    assert all(r["candidate_status"] == r["opponent_status"] == "DONE" for r in rows)
    groups = {(r["opponent_name"], r["arm"], r["seed"], r["candidate_seat"]): r
              for r in rows}
    assert len(groups) == len(jobs)
    comparisons = []
    for name in OPPONENTS:
        for seed in SEEDS:
            for seat in (0, 1):
                a = groups[name, "control", seed, seat]
                b = groups[name, "treatment", seed, seat]
                comparisons.append({
                    "opponent_name": name, "seed": seed, "seat": seat,
                    "control_margin": a["margin"],
                    "treatment_margin": b["margin"],
                    "own_cash_delta": b["candidate_reward"] - a["candidate_reward"],
                    "rival_cash_delta": b["opponent_reward"] - a["opponent_reward"],
                    "control_win": a["margin"] > 0,
                    "treatment_win": b["margin"] > 0,
                    "advanced_turns": (b["candidate_telemetry"] or {}).get("clone_gate_adv_turns", 0),
                })
    summary = {}
    for name in OPPONENTS:
        part = [r for r in comparisons if r["opponent_name"] == name]
        summary[name] = {
            "control_wins": sum(r["control_win"] for r in part),
            "treatment_wins": sum(r["treatment_win"] for r in part),
            "rescues": sum(not r["control_win"] and r["treatment_win"] for r in part),
            "reversals": sum(r["control_win"] and not r["treatment_win"] for r in part),
            "margin_delta": sum(r["treatment_margin"] - r["control_margin"] for r in part),
            "own_cash_delta": sum(r["own_cash_delta"] for r in part),
            "rival_cash_delta": sum(r["rival_cash_delta"] for r in part),
            "advanced_games": sum(r["advanced_turns"] > 0 for r in part),
        }
    OUTPUT.write_text(json.dumps({
        "base_sha256": hashlib.sha256(BASE.read_bytes()).hexdigest(),
        "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        "opponent_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
                            for name, path in OPPONENTS.items()},
        "seeds": SEEDS, "summary": summary,
        "comparisons": comparisons, "rows": rows,
    }, indent=2), encoding="utf8")
    print(json.dumps(summary, indent=2))
    print(OUTPUT)


if __name__ == "__main__":
    main()
