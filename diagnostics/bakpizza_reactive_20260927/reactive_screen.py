"""Both-seat native A/B against a reacting main.py on preselected shops."""

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
CANDIDATE = ROOT / "exp_route_bakpizza_101_20260927.py"
MAIN_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
CANDIDATE_HASH = "dfd82dd45769379f39adc299e90b8c721f2eff7e352b4070699aff81cbd72c9c"
TARGET = ["BAKERY", "PIZZA_SHOP"]


def play(job: tuple[str, int, int]) -> dict:
    arm, seed, seat = job
    result = run_game(str(MAIN if arm == "control" else CANDIDATE),
                      str(MAIN), seed, seat, False, 144, {})
    capture = result["candidate_capture"]
    return {
        "arm": arm, "seed": seed, "seat": seat,
        "shops": capture["shops"][:2] if capture else None,
        "own_cash": result["candidate_reward"],
        "rival_cash": result["opponent_reward"],
        "margin": result["margin"],
        "statuses": [result["candidate_status"], result["opponent_status"]],
        "max_candidate_ms": result["candidate_timing"]["max_ms"],
    }


def main() -> None:
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == MAIN_HASH
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == CANDIDATE_HASH
    selection = json.loads((HERE / "seed_selection.json").read_text(encoding="utf8"))
    seeds = selection["selected"]
    assert len(seeds) == 6 and len(set(seeds)) == 6
    jobs = [(arm, seed, seat) for arm in ("control", "candidate")
            for seed in seeds for seat in (0, 1)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    rows.sort(key=lambda row: (row["seed"], row["seat"], row["arm"]))
    assert len(rows) == 24
    assert all(row["shops"] == TARGET and row["statuses"] == ["DONE", "DONE"]
               for row in rows)
    by = {(row["arm"], row["seed"], row["seat"]): row for row in rows}
    comparisons = []
    for seed in seeds:
        for seat in (0, 1):
            old = by[("control", seed, seat)]
            new = by[("candidate", seed, seat)]
            comparisons.append({"seed": seed, "seat": seat,
                                "old_own": old["own_cash"], "new_own": new["own_cash"],
                                "old_rival": old["rival_cash"], "new_rival": new["rival_cash"],
                                "old_margin": old["margin"], "new_margin": new["margin"],
                                "delta_own": new["own_cash"] - old["own_cash"],
                                "delta_rival": new["rival_cash"] - old["rival_cash"],
                                "delta_margin": new["margin"] - old["margin"]})
    paired = []
    for seed in seeds:
        pair = [r for r in comparisons if r["seed"] == seed]
        paired.append({"seed": seed,
                       "own_cash_delta": sum(r["delta_own"] for r in pair),
                       "rival_cash_delta": sum(r["delta_rival"] for r in pair),
                       "margin_delta": sum(r["delta_margin"] for r in pair)})
    total_own = sum(r["delta_own"] for r in comparisons)
    total_margin = sum(r["delta_margin"] for r in comparisons)
    positive_seeds = sum(r["margin_delta"] > 0 for r in paired)
    min_paired_margin = min(r["margin_delta"] for r in paired)
    gate = (total_own > 0 and total_margin > 0 and positive_seeds >= 4
            and min_paired_margin >= -5000)
    summary = {"total_own_cash_delta": total_own,
               "total_rival_cash_delta": sum(r["delta_rival"] for r in comparisons),
               "total_margin_delta": total_margin,
               "positive_paired_seeds": positive_seeds,
               "min_paired_margin_delta": min_paired_margin,
               "gate_pass": gate}
    payload = {"main_sha256": MAIN_HASH, "candidate_sha256": CANDIDATE_HASH,
               "seeds": seeds, "summary": summary, "paired": paired,
               "comparisons": comparisons, "rows": rows}
    (HERE / "reactive_dev6.json").write_text(json.dumps(payload, indent=2), encoding="utf8")
    for row in paired:
        print(row, flush=True)
    print(summary, flush=True)


if __name__ == "__main__":
    main()
