"""Fresh both-seat native A/B of current mirror24 versus uploaded mirror12."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

CURRENT = ROOT / "main.py"
PREVIOUS = ROOT / "main_before_mirror_straw24_20260926_08aa268a.py"
SEEDS = tuple(range(2612600, 2612624))
OUTPUT = Path(__file__).with_name("reactive_mirror24_retention24.json")
CURRENT_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
PREVIOUS_HASH = "08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863"


def play(job: tuple[int, int]) -> dict:
    seed, seat = job
    return run_game(str(CURRENT), str(PREVIOUS), seed, seat, False, None, {})


def main() -> None:
    assert hashlib.sha256(CURRENT.read_bytes()).hexdigest() == CURRENT_HASH
    assert hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() == PREVIOUS_HASH
    jobs = [(seed, seat) for seed in SEEDS for seat in (0, 1)]
    with ProcessPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(play, jobs))
    assert len(rows) == 48
    assert all(row["candidate_status"] == row["opponent_status"] == "DONE" for row in rows)
    paired = {seed: sum(row["margin"] for row in rows if row["seed"] == seed)
              for seed in SEEDS}
    summary = {
        "paired_seed_positive": sum(value > 0 for value in paired.values()),
        "paired_seed_negative": sum(value < 0 for value in paired.values()),
        "paired_seed_tied": sum(value == 0 for value in paired.values()),
        "seat_wins": sum(row["margin"] > 0 for row in rows),
        "seat_losses": sum(row["margin"] < 0 for row in rows),
        "seat_ties": sum(row["margin"] == 0 for row in rows),
        "total_margin": sum(row["margin"] for row in rows),
        "own_cash": sum(row["candidate_reward"] for row in rows),
        "rival_cash": sum(row["opponent_reward"] for row in rows),
        "max_candidate_call_ms": max(row["candidate_timing"]["max_ms"] for row in rows),
        "candidate_error_games": sum(any(value for key, value in
                                          (row.get("candidate_telemetry") or {}).items()
                                          if key.endswith("errors")) for row in rows),
    }
    OUTPUT.write_text(json.dumps({"current_sha256": CURRENT_HASH,
                                  "previous_sha256": PREVIOUS_HASH,
                                  "seeds": SEEDS, "summary": summary,
                                  "paired_margins": paired, "rows": rows},
                                 indent=2), encoding="utf8")
    print(json.dumps(summary, indent=2))
    print(OUTPUT)


if __name__ == "__main__":
    main()
