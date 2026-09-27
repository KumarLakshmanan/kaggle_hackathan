"""Predeclared native reactive screen of static v48 route data versus main."""

from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402


CURRENT = ROOT / "main.py"
CANDIDATE = Path(__file__).with_name("data_route_candidate.py")
OUTPUT = Path(__file__).with_name("reactive_screen.json")
SEEDS = tuple(range(2614000, 2614008))
CURRENT_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"


def play(job):
    seed, seat = job
    return run_game(str(CANDIDATE), str(CURRENT), seed, seat, False, None, {})


def main():
    assert hashlib.sha256(CURRENT.read_bytes()).hexdigest() == CURRENT_HASH
    jobs = [(seed, seat) for seed in SEEDS for seat in (0, 1)]
    with ProcessPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(play, jobs))
    pairs = {seed: sum(row["margin"] for row in rows if row["seed"] == seed) for seed in SEEDS}
    summary = {
        "paired_wins": sum(value > 0 for value in pairs.values()),
        "paired_losses": sum(value < 0 for value in pairs.values()),
        "paired_ties": sum(value == 0 for value in pairs.values()),
        "seat_wins": sum(row["margin"] > 0 for row in rows),
        "total_margin": sum(row["margin"] for row in rows),
        "own_cash": sum(row["candidate_reward"] for row in rows),
        "rival_cash": sum(row["opponent_reward"] for row in rows),
        "statuses": [[row["candidate_status"], row["opponent_status"]] for row in rows],
        "max_call_ms": max(row["candidate_timing"]["max_ms"] for row in rows),
    }
    OUTPUT.write_text(json.dumps({"current_sha256": CURRENT_HASH, "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(), "source_data_sha256": hashlib.sha256(Path(__file__).with_name("routes_untrusted.json").read_bytes()).hexdigest(), "seeds": SEEDS, "summary": summary, "paired_margins": pairs, "rows": rows}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(OUTPUT)


if __name__ == "__main__":
    main()
