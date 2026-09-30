"""Frozen both-seat native A/B against reacting current main.py."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

MAIN = ROOT / "main.py"
CANDIDATE = ROOT / "exp_physical_milk_sale_20260927.py"
MAIN_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
CANDIDATE_HASH = "d65173e46e531068b85d78ad24ac779ce1cc7b56864dfb361a9eaffae87944a2"
SEEDS = tuple(range(2623000, 2623016))
OUTPUT = HERE / "reactive_dev16.json"


def play(job: tuple[str, int, int]) -> dict:
    arm, seed, seat = job
    game = run_game(str(MAIN if arm == "control" else CANDIDATE),
                    str(MAIN), seed, seat, False, 144, {})
    return {"arm": arm, "seed": seed, "seat": seat,
            "own_cash": game["candidate_reward"],
            "rival_cash": game["opponent_reward"],
            "margin": game["margin"],
            "statuses": [game["candidate_status"], game["opponent_status"]],
            "shops": game["candidate_capture"]["shops"][:2],
            "telemetry": game["candidate_telemetry"],
            "max_candidate_ms": game["candidate_timing"]["max_ms"]}


def main() -> None:
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == MAIN_HASH
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == CANDIDATE_HASH
    jobs = [(arm, seed, seat) for arm in ("control", "candidate")
            for seed in SEEDS for seat in (0, 1)]
    with ProcessPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(play, jobs))
    rows.sort(key=lambda row: (row["seed"], row["seat"], row["arm"]))
    assert len(rows) == 64
    assert all(row["statuses"] == ["DONE", "DONE"] for row in rows)
    by = {(row["arm"], row["seed"], row["seat"]): row for row in rows}
    comparisons = []
    for seed in SEEDS:
        for seat in (0, 1):
            old, new = by[("control", seed, seat)], by[("candidate", seed, seat)]
            assert old["shops"] == new["shops"]
            comparisons.append({"seed": seed, "seat": seat,
                                "shops": new["shops"],
                                "old_margin": old["margin"],
                                "new_margin": new["margin"],
                                "delta_own": new["own_cash"]-old["own_cash"],
                                "delta_rival": new["rival_cash"]-old["rival_cash"],
                                "delta_margin": new["margin"]-old["margin"],
                                "triggered": new["telemetry"].get("triggered", 0),
                                "units": new["telemetry"].get("sold_units", new["telemetry"].get("units", 0)),
                                "errors": new["telemetry"].get("errors", 0)})
    paired = []
    for seed in SEEDS:
        subset = [row for row in comparisons if row["seed"] == seed]
        paired.append({"seed": seed,
                       "triggered": sum(row["triggered"] for row in subset),
                       "units": sum(row["units"] for row in subset),
                       "errors": sum(row["errors"] for row in subset),
                       "delta_own": sum(row["delta_own"] for row in subset),
                       "delta_rival": sum(row["delta_rival"] for row in subset),
                       "delta_margin": sum(row["delta_margin"] for row in subset)})
    activated = [row for row in paired if row["triggered"]]
    positive = sum(row["delta_margin"] > 0 for row in activated)
    total_own = sum(row["delta_own"] for row in activated)
    total_margin = sum(row["delta_margin"] for row in activated)
    worst = min((row["delta_margin"] for row in activated), default=0)
    errors = sum(row["errors"] for row in paired)
    gate = (len(activated) >= 4 and errors == 0 and total_own > 0 and total_margin > 0
            and positive * 3 >= len(activated) * 2 and worst >= -5000)
    summary = {"activated_paired_seeds": len(activated),
               "positive_activated_paired_seeds": positive,
               "total_own_delta_activated": total_own,
               "total_rival_delta_activated": sum(row["delta_rival"] for row in activated),
               "total_margin_delta_activated": total_margin,
               "worst_activated_paired_margin_delta": worst,
               "triggered_orders": sum(row["triggered"] for row in paired),
               "triggered_units": sum(row["units"] for row in paired),
               "errors": errors,
               "gate_pass": gate}
    payload = {"main_sha256": MAIN_HASH, "candidate_sha256": CANDIDATE_HASH,
               "seeds": SEEDS, "summary": summary,
               "paired": paired, "comparisons": comparisons, "rows": rows}
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf8")
    for pair in paired:
        print(pair, flush=True)
    print(summary, flush=True)


if __name__ == "__main__":
    main()
