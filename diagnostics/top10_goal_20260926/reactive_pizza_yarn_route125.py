"""Matched native A/B for the preselected PIZZA_SHOP,YARN_STORE seeds."""

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
CANDIDATE = ROOT / "exp_pizza_yarn_route125_20260926.py"


def play(job: tuple[str, int, int]) -> dict:
    arm, seed, seat = job
    row = run_game(
        candidate=str(BASE if arm == "control" else CANDIDATE),
        opponent=str(BASE), seed=seed, candidate_seat=seat,
        debug=False, capture_step=144, candidate_overrides={},
    )
    row["arm"] = arm
    return row


def main() -> None:
    selection = json.loads((OUT / "native_pizza_yarn_seeds.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == selection["main_sha256"]
    seeds = selection["selected"]
    assert len(seeds) == 4 and len(set(seeds)) == 4
    jobs = [(arm, seed, seat) for arm in ("control", "treatment")
            for seed in seeds for seat in (0, 1)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    rows.sort(key=lambda r: (r["arm"], r["seed"], r["candidate_seat"]))
    assert all(r["candidate_status"] == r["opponent_status"] == "DONE" for r in rows)
    control = {(r["seed"], r["candidate_seat"]): r for r in rows if r["arm"] == "control"}
    treatment = {(r["seed"], r["candidate_seat"]): r for r in rows if r["arm"] == "treatment"}
    assert len(control) == len(treatment) == 2 * len(seeds)
    comparisons = []
    for key in sorted(control):
        base, candidate = control[key], treatment[key]
        assert candidate["candidate_capture"]["shops"][:2] == ["PIZZA_SHOP", "YARN_STORE"], key
        assert candidate["candidate_telemetry"].get("route125_turns", 0) > 0, key
        comparisons.append({
            "seed": key[0], "seat": key[1],
            "control_margin": base["margin"], "treatment_margin": candidate["margin"],
            "own_cash_delta": candidate["candidate_reward"] - base["candidate_reward"],
            "rival_cash_delta": candidate["opponent_reward"] - base["opponent_reward"],
        })
    payload = {
        "base_sha256": hashlib.sha256(BASE.read_bytes()).hexdigest(),
        "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        "selection": selection, "rows": rows, "comparisons": comparisons,
    }
    (OUT / "reactive_pizza_yarn_route125.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("control wins", sum(r["margin"] > 0 for r in control.values()))
    print("treatment wins", sum(r["margin"] > 0 for r in treatment.values()))
    print("own cash delta", sum(c["own_cash_delta"] for c in comparisons))
    print("rival cash delta", sum(c["rival_cash_delta"] for c in comparisons))
    print("route125 turns", sum(r["candidate_telemetry"]["route125_turns"] for r in treatment.values()))
    print("max candidate call ms", max(r["candidate_timing"]["max_ms"] for r in treatment.values()))


if __name__ == "__main__":
    main()
