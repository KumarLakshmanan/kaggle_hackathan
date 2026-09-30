"""Native both-seat matchups against diverse saved public agents."""

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

MAIN = ROOT / "main.py"
PUBLIC = ROOT / "kaggle_complete_agents_live_2026-09-23_page6_top100"
OPPONENTS = {
    "thomas_2945": PUBLIC
    / "087-thomastschinkel__the-2945-farm-96-vs-the-top-10-public-bots__6b335138cfb4.py",
    "aurax7_router_v6": PUBLIC
    / "068-aurax7__kaggriculture-shop-router-reactive-v6__0bb12762c2ea.py",
    "foysal_2727": PUBLIC
    / "003-foysalemonshanto__last-day-lb-2727-2__69c8de95a37a.py",
}
SEEDS = tuple(range(2610700, 2610704))
OUTPUT = Path(__file__).with_name("public_native_panel.json")


def play(job):
    name, seed, seat = job
    row = run_game(str(MAIN), str(OPPONENTS[name]), seed, seat, False, None, {})
    row["opponent_name"] = name
    return row


def main():
    jobs = [(name, seed, seat)
            for name in OPPONENTS for seed in SEEDS for seat in (0, 1)]
    rows = []
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(play, job): job for job in jobs}
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(f"{row['opponent_name']} seed={row['seed']} "
                  f"seat={row['candidate_seat']} margin={row['margin']:+.0f} "
                  f"status={row['candidate_status']}/{row['opponent_status']}",
                  flush=True)
    assert len(rows) == len(jobs)
    summary = {}
    for name in OPPONENTS:
        part = [r for r in rows if r["opponent_name"] == name]
        summary[name] = {
            "games": len(part),
            "wins": sum(r["margin"] > 0 for r in part),
            "losses": sum(r["margin"] < 0 for r in part),
            "draws": sum(r["margin"] == 0 for r in part),
            "margin_sum": sum(r["margin"] for r in part),
            "own_cash_sum": sum(r["candidate_reward"] for r in part),
            "rival_cash_sum": sum(r["opponent_reward"] for r in part),
            "all_done": all(r["candidate_status"] == r["opponent_status"] == "DONE"
                            for r in part),
        }
    result = {
        "main_sha256": hashlib.sha256(MAIN.read_bytes()).hexdigest(),
        "opponent_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
                            for name, path in OPPONENTS.items()},
        "seeds": SEEDS,
        "summary": summary,
        "rows": rows,
    }
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps(summary, indent=2))
    print(OUTPUT)


if __name__ == "__main__":
    main()
