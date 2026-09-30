"""Native reactive test of the physical-mirror-gated sale advance."""

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
SEEDS = tuple(range(2609200, 2609208))


def play(job: tuple[int, int]) -> dict:
    seed, seat = job
    return run_game(candidate=str(CANDIDATE), opponent=str(BASE), seed=seed,
                    candidate_seat=seat, debug=False, capture_step=None,
                    candidate_overrides={})


def main() -> None:
    jobs = [(seed, seat) for seed in SEEDS for seat in (0, 1)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    rows.sort(key=lambda r: (r["seed"], r["candidate_seat"]))
    assert len(rows) == 16
    assert all(r["candidate_status"] == r["opponent_status"] == "DONE" for r in rows)
    previous = json.loads((OUT / "reactive_look8_native.json").read_text(encoding="utf-8"))
    controls = {(r["seed"], r["candidate_seat"]): r for r in previous["rows"] if r["arm"] == "control"}
    assert len(controls) == 16
    comparisons = []
    for r in rows:
        key = r["seed"], r["candidate_seat"]
        a = controls[key]
        comparisons.append({
            "seed": key[0], "seat": key[1],
            "control_margin": a["margin"], "treatment_margin": r["margin"],
            "own_cash_delta": r["candidate_reward"] - a["candidate_reward"],
            "rival_cash_delta": r["opponent_reward"] - a["opponent_reward"],
            "equal_turns": r["candidate_telemetry"].get("clone_gate_equal_turns", 0),
            "active_advance_turns": r["candidate_telemetry"].get("clone_gate_adv_turns", 0),
        })
    payload = {"base_sha256": hashlib.sha256(BASE.read_bytes()).hexdigest(),
               "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
               "seeds": SEEDS, "rows": rows, "comparisons": comparisons}
    (OUT / "reactive_clonegate_native.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("treatment wins", sum(r["margin"] > 0 for r in rows), "/", len(rows))
    print("own cash delta", sum(c["own_cash_delta"] for c in comparisons))
    print("rival cash delta", sum(c["rival_cash_delta"] for c in comparisons))
    print("equal turns", sum(c["equal_turns"] for c in comparisons))
    print("active advance turns", sum(c["active_advance_turns"] for c in comparisons))
    print("max candidate call ms", max(r["candidate_timing"]["max_ms"] for r in rows))


if __name__ == "__main__":
    main()
