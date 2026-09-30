"""Matched fresh reactive comparison of six- and eight-turn mirror gates."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

OUT = Path(__file__).resolve().parent
BASE = ROOT / "main_before_top10_goal_20260926_04b0bdc3.py"
ARMS = {
    "control": BASE,
    "mirror8": ROOT / "main.py",
    "mirror6": ROOT / "exp_sale_mirror6_20260926.py",
}
SEEDS = tuple(range(2610000, 2610008))


def play(job: tuple[str, int, int]) -> dict:
    arm, seed, seat = job
    row = run_game(
        candidate=str(ARMS[arm]), opponent=str(BASE), seed=seed,
        candidate_seat=seat, debug=False, capture_step=None,
        candidate_overrides={},
    )
    row["arm"] = arm
    return row


def main() -> None:
    jobs = [(arm, seed, seat) for arm in ARMS for seed in SEEDS for seat in (0, 1)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    rows.sort(key=lambda r: (r["arm"], r["seed"], r["candidate_seat"]))
    assert len(rows) == 48
    assert all(r["candidate_status"] == r["opponent_status"] == "DONE" for r in rows)
    by_arm = {
        arm: {(r["seed"], r["candidate_seat"]): r for r in rows if r["arm"] == arm}
        for arm in ARMS
    }
    assert all(len(games) == 16 for games in by_arm.values())
    assert all(set(games) == set(by_arm["control"]) for games in by_arm.values())
    comparisons = []
    for key in sorted(by_arm["control"]):
        base = by_arm["control"][key]
        comp = {"seed": key[0], "seat": key[1], "control_margin": base["margin"]}
        for arm in ("mirror8", "mirror6"):
            trial = by_arm[arm][key]
            comp[arm] = {
                "margin": trial["margin"],
                "own_cash_delta": trial["candidate_reward"] - base["candidate_reward"],
                "rival_cash_delta": trial["opponent_reward"] - base["opponent_reward"],
                "advance_turns": trial["candidate_telemetry"].get("clone_gate_adv_turns", 0),
            }
        comparisons.append(comp)
    summary = {}
    for arm in ARMS:
        games = by_arm[arm].values()
        summary[arm] = {
            "wins": sum(r["margin"] > 0 for r in games),
            "margin_sum": sum(r["margin"] for r in games),
            "own_cash_sum": sum(r["candidate_reward"] for r in games),
            "rival_cash_sum": sum(r["opponent_reward"] for r in games),
            "max_candidate_call_ms": max(r["candidate_timing"]["max_ms"] for r in games),
        }
        if arm != "control":
            summary[arm]["advance_turns"] = sum(
                r["candidate_telemetry"].get("clone_gate_adv_turns", 0) for r in games
            )
            summary[arm]["activated_games"] = sum(
                r["candidate_telemetry"].get("clone_gate_adv_turns", 0) > 0 for r in games
            )
    payload = {
        "policy_hashes": {arm: hashlib.sha256(path.read_bytes()).hexdigest()
                          for arm, path in ARMS.items()},
        "seeds": SEEDS, "summary": summary,
        "comparisons": comparisons, "rows": rows,
    }
    dest = OUT / "reactive_mirror6_fresh.json"
    dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(dest)


if __name__ == "__main__":
    main()
