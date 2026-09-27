"""Screen the complete saved DSM action schedule against reacting main.py."""

from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

MAIN = ROOT / "main.py"
ROUTE = ROOT / "diagnostics/top100_refresh_2026-09-26" / (
    "DSM-submission-56557996-episode-113531265-seat1.json.gz")
SEEDS = tuple(range(2610940, 2610948))
OUTPUT = Path(__file__).with_name("dsm_raw_native_screen.json")


def play(job):
    seed, seat = job
    row = run_game(f"rawroute:{ROUTE}", str(MAIN), seed, seat, False, 144, {})
    capture = row.pop("candidate_capture")
    row["shops_at_day6"] = capture["shops"] if capture else None
    row["day6_counts"] = (capture["farms"][seat]["counts"] if capture else None)
    return row


def main():
    jobs = [(seed, seat) for seed in SEEDS for seat in (0, 1)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    assert len(rows) == len(jobs)
    print(json.dumps([
        {"seed": r["seed"], "seat": r["candidate_seat"],
         "shops": r["shops_at_day6"], "margin": r["margin"],
         "status": [r["candidate_status"], r["opponent_status"]]}
        for r in rows
    ], indent=2), flush=True)
    summary = {
        "wins": sum(r["margin"] > 0 for r in rows),
        "losses": sum(r["margin"] < 0 for r in rows),
        "margin_sum": sum(r["margin"] for r in rows),
        "all_done": all(r["candidate_status"] == r["opponent_status"] == "DONE"
                        for r in rows),
    }
    OUTPUT.write_text(json.dumps({
        "main_sha256": hashlib.sha256(MAIN.read_bytes()).hexdigest(),
        "route_sha256": hashlib.sha256(ROUTE.read_bytes()).hexdigest(),
        "seeds": SEEDS, "summary": summary, "rows": rows,
    }, indent=2), encoding="utf8")
    print(summary)
    print(OUTPUT)


if __name__ == "__main__":
    main()
