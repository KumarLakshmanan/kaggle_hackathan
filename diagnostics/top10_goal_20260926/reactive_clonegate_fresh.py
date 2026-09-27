"""Predeclared fresh native seeds for the observation-only mirror gate."""

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
BASE = ROOT / "main.py"
CANDIDATE = ROOT / "exp_sale_look8_clonegated_20260926.py"
SEEDS = tuple(range(2609300, 2609308))


def play(job: tuple[str, int, int]) -> dict:
    arm, seed, seat = job
    result = run_game(candidate=str(BASE if arm == "control" else CANDIDATE),
                      opponent=str(BASE), seed=seed, candidate_seat=seat,
                      debug=False, capture_step=None, candidate_overrides={})
    result["arm"] = arm
    return result


def main() -> None:
    jobs = [(arm, seed, seat) for arm in ("control", "treatment")
            for seed in SEEDS for seat in (0, 1)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    rows.sort(key=lambda r: (r["arm"], r["seed"], r["candidate_seat"]))
    assert len(rows) == 32
    assert all(r["candidate_status"] == r["opponent_status"] == "DONE" for r in rows)
    controls = {(r["seed"], r["candidate_seat"]): r for r in rows if r["arm"] == "control"}
    treatment = {(r["seed"], r["candidate_seat"]): r for r in rows if r["arm"] == "treatment"}
    assert len(controls) == len(treatment) == 16
    comparisons = []
    for key in sorted(controls):
        a, b = controls[key], treatment[key]
        comparisons.append({
            "seed": key[0], "seat": key[1],
            "control_margin": a["margin"], "treatment_margin": b["margin"],
            "own_cash_delta": b["candidate_reward"] - a["candidate_reward"],
            "rival_cash_delta": b["opponent_reward"] - a["opponent_reward"],
            "equal_turns": b["candidate_telemetry"].get("clone_gate_equal_turns", 0),
            "active_advance_turns": b["candidate_telemetry"].get("clone_gate_adv_turns", 0),
        })
    payload = {"base_sha256": hashlib.sha256(BASE.read_bytes()).hexdigest(),
               "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
               "seeds": SEEDS, "rows": rows, "comparisons": comparisons}
    (OUT / "reactive_clonegate_fresh.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("control wins", sum(r["margin"] > 0 for r in controls.values()))
    print("treatment wins", sum(r["margin"] > 0 for r in treatment.values()))
    print("own cash delta", sum(c["own_cash_delta"] for c in comparisons))
    print("rival cash delta", sum(c["rival_cash_delta"] for c in comparisons))
    print("active advance turns", sum(c["active_advance_turns"] for c in comparisons))
    print("min/max margin", min(r["margin"] for r in treatment.values()),
          max(r["margin"] for r in treatment.values()))
    print("max candidate call ms", max(r["candidate_timing"]["max_ms"] for r in treatment.values()))


if __name__ == "__main__":
    main()
