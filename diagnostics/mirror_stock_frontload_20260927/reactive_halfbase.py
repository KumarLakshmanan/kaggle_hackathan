"""Frozen fresh 16-seed both-seat reactive screen for half-base stock sale."""

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402


CURRENT = ROOT / "main.py"
CANDIDATE = ROOT / "exp_mirror_stock_frontload_halfbase_20260927.py"
OUTPUT = Path(__file__).with_name("reactive_halfbase.json")
SEEDS = tuple(range(2614300, 2614316))
CURRENT_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
CANDIDATE_HASH = "e9517daebe5523879c5096839570af04619135fc7f5a7fb7e6446ab1c367ca68"


def play(job):
    seed, seat = job
    return run_game(str(CANDIDATE), str(CURRENT), seed, seat, False, None, {})


def main():
    assert hashlib.sha256(CURRENT.read_bytes()).hexdigest() == CURRENT_HASH
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == CANDIDATE_HASH
    jobs = [(seed, seat) for seed in SEEDS for seat in (0, 1)]
    rows = []
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(play, job): job for job in jobs}
        for completed in as_completed(futures):
            row = completed.result()
            rows.append(row)
            print("seed", row["seed"], "seat", row["candidate_seat"],
                  "margin", row["margin"], "trigger",
                  (row.get("candidate_telemetry") or {}).get("latch_trigger_turns"),
                  "status", row["candidate_status"], row["opponent_status"], flush=True)
    rows.sort(key=lambda row: (row["seed"], row["candidate_seat"]))
    pairs = {seed: sum(row["margin"] for row in rows if row["seed"] == seed)
             for seed in SEEDS}
    summary = {
        "paired_wins": sum(value > 0 for value in pairs.values()),
        "paired_losses": sum(value < 0 for value in pairs.values()),
        "paired_ties": sum(value == 0 for value in pairs.values()),
        "seat_wins": sum(row["margin"] > 0 for row in rows),
        "total_margin": sum(row["margin"] for row in rows),
        "own_cash": sum(row["candidate_reward"] for row in rows),
        "rival_cash": sum(row["opponent_reward"] for row in rows),
        "all_done": all(row["candidate_status"] == row["opponent_status"] == "DONE"
                        for row in rows),
        "error_games": sum(any(key.endswith("errors") and value
                               for key, value in (row.get("candidate_telemetry") or {}).items())
                           for row in rows),
        "trigger_games": sum((row.get("candidate_telemetry") or {}).get("latch_trigger_turns", 0) > 0
                             for row in rows),
        "max_call_ms": max(row["candidate_timing"]["max_ms"] for row in rows),
    }
    OUTPUT.write_text(json.dumps({"current_sha256": CURRENT_HASH,
                                  "candidate_sha256": CANDIDATE_HASH,
                                  "seeds": SEEDS, "summary": summary,
                                  "paired_margins": pairs, "rows": rows}, indent=2),
                      encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(OUTPUT)


if __name__ == "__main__":
    main()
