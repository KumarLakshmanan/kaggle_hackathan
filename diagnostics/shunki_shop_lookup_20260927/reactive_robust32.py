"""Untouched descriptive 32-seed robustness check for the frozen lookup."""

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
CANDIDATE = ROOT / "exp_shunki_shop_lookup_20260927.py"
MAIN_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
SEEDS = tuple(range(2630100, 2630132))


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
    build = json.loads((HERE / "build_manifest.json").read_text(encoding="utf8"))
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == MAIN_HASH
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == build["candidate_sha256"]
    assert (HERE / "candidate_parity.json").is_file()
    jobs = [(arm, seed, seat) for arm in ("control", "candidate")
            for seed in SEEDS for seat in (0, 1)]
    rows = []
    with ProcessPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(play, job): job for job in jobs}
        for future in as_completed(futures):
            rows.append(future.result())
            if len(rows) % 8 == 0:
                (HERE / "robust_partial.json").write_text(
                    json.dumps({"completed": len(rows), "rows": rows}, indent=2),
                    encoding="utf8")
                print(f"completed {len(rows)}/{len(jobs)}", flush=True)
    by = {(row["arm"], row["seed"], row["seat"]): row for row in rows}
    comparisons = []
    paired = []
    for seed in SEEDS:
        seed_rows = []
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
            seed_rows.append(row)
            comparisons.append(row)
        paired.append({"seed": seed,
                       "delta_own": sum(row["delta_own"] for row in seed_rows),
                       "delta_rival": sum(row["delta_rival"] for row in seed_rows),
                       "delta_margin": sum(row["delta_margin"] for row in seed_rows),
                       "both_done": all(row["statuses"] == ["DONE", "DONE"]
                                        for row in seed_rows)})
    all_done = all(row["statuses"] == ["DONE", "DONE"] for row in rows)
    same_shops = sum(row["shops_candidate"] == row["shops_control"]
                     for row in comparisons)
    positive_pairs = sum(row["delta_margin"] > 0 for row in paired)
    positive_seats = sum(row["delta_margin"] > 0 for row in comparisons)
    own_delta = sum(row["delta_own"] for row in paired)
    rival_delta = sum(row["delta_rival"] for row in paired)
    margin_delta = sum(row["delta_margin"] for row in paired)
    worst = min(row["delta_margin"] for row in paired)
    summary = {"all_done": all_done, "same_first_two_shops": same_shops,
               "paired_seed_wins": positive_pairs, "seat_wins": positive_seats,
               "total_delta_own": own_delta, "total_delta_rival": rival_delta,
               "total_delta_margin": margin_delta,
               "worst_paired_delta_margin": worst,
               "max_candidate_ms": max(row["max_candidate_ms"] for row in rows
                                       if row["arm"] == "candidate")}
    result = {"main_sha256": MAIN_HASH,
              "candidate_sha256": build["candidate_sha256"],
              "seeds": SEEDS, "summary": summary,
              "paired": paired, "comparisons": comparisons,
              "rows": sorted(rows, key=lambda row: (row["arm"], row["seed"], row["seat"]))}
    (HERE / "reactive_robust32.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    for row in paired:
        print(row, flush=True)
    print(summary, flush=True)


if __name__ == "__main__":
    main()
