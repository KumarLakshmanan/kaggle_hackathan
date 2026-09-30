"""Predeclared 16-seed, both-seat native check of mirror lookahead 16 vs 12."""

from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

BASE = ROOT / "main.py"
CANDIDATE = ROOT / "exp_sale_mirror16_20260926.py"
SEEDS = tuple(range(2610600, 2610616))
OUTPUT = Path(__file__).with_name("reactive_mirror16_fresh.json")


def play(job):
    seed, seat = job
    return run_game(str(CANDIDATE), str(BASE), seed, seat, False, None, {})


def main():
    jobs = [(seed, seat) for seed in SEEDS for seat in (0, 1)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    assert len(rows) == 32
    assert all(r["candidate_status"] == r["opponent_status"] == "DONE" for r in rows)
    summary = {
        "wins": sum(r["margin"] > 0 for r in rows),
        "losses": sum(r["margin"] < 0 for r in rows),
        "draws": sum(r["margin"] == 0 for r in rows),
        "margin_sum": sum(r["margin"] for r in rows),
        "own_cash_sum": sum(r["candidate_reward"] for r in rows),
        "rival_cash_sum": sum(r["opponent_reward"] for r in rows),
        "max_candidate_call_ms": max(r["candidate_timing"]["max_ms"] for r in rows),
        "advanced_games": sum((r["candidate_telemetry"] or {}).get("clone_gate_adv_turns", 0) > 0
                              for r in rows),
        "advance_errors": sum((r["candidate_telemetry"] or {}).get("clone_gate_errors", 0)
                              + (r["candidate_telemetry"] or {}).get("adv_errors", 0)
                              for r in rows),
    }
    OUTPUT.write_text(json.dumps({
        "base_sha256": hashlib.sha256(BASE.read_bytes()).hexdigest(),
        "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        "seeds": SEEDS, "summary": summary, "rows": rows,
    }, indent=2), encoding="utf8")
    print(json.dumps(summary, indent=2))
    print(OUTPUT)


if __name__ == "__main__":
    main()
