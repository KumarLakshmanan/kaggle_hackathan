"""Untouched arbitrary-shop native confirmation for the packaged route."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

MAIN = ROOT / "main.py"
CANDIDATE = ROOT / "exp_shunki_public_route_20260927.py"
MAIN_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
CANDIDATE_HASH = "39d39bfdcb40b782785b8be50e03b925c19b1510bb1610e7704ebb8bfbef8744"
SEEDS = tuple(range(2629000, 2629016))


def play(job: tuple[str, int, int]) -> dict:
    arm, seed, seat = job
    path = MAIN if arm == "control" else CANDIDATE
    game = run_game(str(path), str(MAIN), seed, seat, False, 144, {})
    return {"arm": arm, "seed": seed, "seat": seat,
            "own_cash": game["candidate_reward"],
            "rival_cash": game["opponent_reward"],
            "margin": game["margin"],
            "statuses": [game["candidate_status"], game["opponent_status"]],
            "shops_at_day6": game["candidate_capture"]["shops"][:2],
            "max_candidate_ms": game["candidate_timing"]["max_ms"]}


def main() -> None:
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == MAIN_HASH
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == CANDIDATE_HASH
    jobs = [(arm, seed, seat) for arm in ("control", "candidate")
            for seed in SEEDS for seat in (0, 1)]
    rows = []
    with ProcessPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(play, job): job for job in jobs}
        for future in as_completed(futures):
            rows.append(future.result())
            if len(rows) % 8 == 0:
                (HERE / "confirm_partial.json").write_text(
                    json.dumps({"completed": len(rows), "rows": rows}, indent=2), encoding="utf8")
                print(f"completed {len(rows)}/{len(jobs)}", flush=True)
    by = {(row["arm"], row["seed"], row["seat"]): row for row in rows}
    comparisons = []
    paired = []
    for seed in SEEDS:
        pair = []
        for seat in (0, 1):
            base = by[("control", seed, seat)]
            trial = by[("candidate", seed, seat)]
            row = {"seed": seed, "seat": seat,
                   "control_margin": base["margin"],
                   "candidate_margin": trial["margin"],
                   "delta_own": trial["own_cash"] - base["own_cash"],
                   "delta_rival": trial["rival_cash"] - base["rival_cash"],
                   "delta_margin": trial["margin"] - base["margin"],
                   "shops_control": base["shops_at_day6"],
                   "shops_candidate": trial["shops_at_day6"],
                   "statuses": trial["statuses"]}
            pair.append(row)
            comparisons.append(row)
        paired.append({"seed": seed,
                       "delta_own": sum(row["delta_own"] for row in pair),
                       "delta_rival": sum(row["delta_rival"] for row in pair),
                       "delta_margin": sum(row["delta_margin"] for row in pair),
                       "both_done": all(row["statuses"] == ["DONE", "DONE"] for row in pair)})
    all_done = all(row["statuses"] == ["DONE", "DONE"] for row in rows)
    paired_wins = sum(row["delta_margin"] > 0 for row in paired)
    seat_wins = sum(row["delta_margin"] > 0 for row in comparisons)
    total_own = sum(row["delta_own"] for row in paired)
    total_rival = sum(row["delta_rival"] for row in paired)
    total_margin = sum(row["delta_margin"] for row in paired)
    worst = min(row["delta_margin"] for row in paired)
    gate = (all_done and paired_wins >= 12 and seat_wins >= 24
            and total_own > 0 and worst >= -10000)
    summary = {"paired_seed_wins": paired_wins, "seat_wins": seat_wins,
               "total_delta_own": total_own, "total_delta_rival": total_rival,
               "total_delta_margin": total_margin,
               "worst_paired_delta_margin": worst,
               "all_done": all_done,
               "same_first_two_shops": sum(row["shops_candidate"] == row["shops_control"]
                                            for row in comparisons),
               "max_candidate_ms": max(row["max_candidate_ms"] for row in rows if row["arm"] == "candidate"),
               "gate_pass": gate}
    result = {"main_sha256": MAIN_HASH, "candidate_sha256": CANDIDATE_HASH,
              "seeds": SEEDS, "summary": summary,
              "paired": paired, "comparisons": comparisons,
              "rows": sorted(rows, key=lambda row: (row["arm"], row["seed"], row["seat"]))}
    (HERE / "reactive_confirm16.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    for row in paired:
        print(row, flush=True)
    print(summary, flush=True)


if __name__ == "__main__":
    main()
