"""Fresh outcome-based comparison against four reacting policies."""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import engine_version, run_game

MAIN = ROOT / "main.py"
CANDIDATE = ROOT / "exp_shunki_later_lookup_20260927.py"
SEEDS = tuple(range(2631000, 2631032))
OPPONENTS = {
    "current_main": MAIN,
    "previous_main": ROOT / "main_uploaded_entrypoint_fix_20260926_08aa268a.py",
    "public_v35": ROOT / "diagnostics/public_ahmed_v35_20260927/public_v35_main.py",
    "public_c95": ROOT / "diagnostics/public_rayk_top_meta/public_c95_main.py",
}
EXPECTED = {
    MAIN: "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b",
    CANDIDATE: "68aad0908c38884aba856373088f1a6ba4a0423df2ee00edbec4c796f8e45fac",
    OPPONENTS["public_v35"]: "294e7e4d9d4b97413646960d318043e0f9116ce58f42fe02afd4716614a4e96d",
    OPPONENTS["public_c95"]: "489f5d197527f107027626cce79d850fd2ca90edd43d94384b849b6511e27bdb",
}


def play(job):
    arm, opponent, seed, seat = job
    result = run_game(str(MAIN if arm == "incumbent" else CANDIDATE),
                      str(OPPONENTS[opponent]), seed, seat, False, 144, {})
    margin = result["margin"]
    return {
        "arm": arm, "opponent": opponent, "seed": seed, "seat": seat,
        "points": 1.0 if margin > 0 else 0.5 if margin == 0 else 0.0,
        "own_cash": result["candidate_reward"],
        "rival_cash": result["opponent_reward"], "margin": margin,
        "statuses": [result["candidate_status"], result["opponent_status"]],
        "shops": (result["candidate_capture"] or {}).get("shops", [])[:2],
        "max_ms": result["candidate_timing"]["max_ms"],
    }


def main():
    assert engine_version == "1.32.7", engine_version
    for path, expected in EXPECTED.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path
    hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in set(OPPONENTS.values()) | {CANDIDATE}}
    manifest = {"engine_version": engine_version, "seeds": SEEDS, "hashes": hashes,
                "plan_sha256": hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest()}
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    jobs = [(arm, opponent, seed, seat) for opponent in OPPONENTS
            for seed in SEEDS for arm in ("incumbent", "candidate") for seat in (0, 1)]
    rows = []
    with ProcessPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(play, job): job for job in jobs}
        for future in as_completed(futures):
            rows.append(future.result())
            if len(rows) % 16 == 0:
                (HERE / "partial.json").write_text(json.dumps({"rows": rows}, indent=2), encoding="utf8")
                print(f"completed {len(rows)}/{len(jobs)}", flush=True)
    by = {(r["arm"], r["opponent"], r["seed"], r["seat"]): r for r in rows}
    per_opponent = {}
    seed_deltas = {seed: 0.0 for seed in SEEDS}
    for opponent in OPPONENTS:
        item = {}
        for arm in ("incumbent", "candidate"):
            selected = [r for r in rows if r["arm"] == arm and r["opponent"] == opponent]
            item[arm] = {"seed_block_points": sum(r["points"] for r in selected) / 2,
                         "seat_wins": sum(r["points"] == 1 for r in selected),
                         "seat_draws": sum(r["points"] == 0.5 for r in selected),
                         "seat_losses": sum(r["points"] == 0 for r in selected),
                         "mean_cash_margin": sum(r["margin"] for r in selected) / len(selected)}
        item["delta_seed_block_points"] = item["candidate"]["seed_block_points"] - item["incumbent"]["seed_block_points"]
        per_opponent[opponent] = item
        for seed in SEEDS:
            seed_deltas[seed] += sum(by[("candidate", opponent, seed, s)]["points"] -
                                     by[("incumbent", opponent, seed, s)]["points"]
                                     for s in (0, 1)) / (2 * len(OPPONENTS))
    deltas = list(seed_deltas.values())
    rng = random.Random(2631032)
    boot = sorted(sum(rng.choices(deltas, k=len(deltas))) / len(deltas) for _ in range(20000))
    interval = [boot[int(0.025 * len(boot))], boot[int(0.975 * len(boot))]]
    all_done = all(r["statuses"] == ["DONE", "DONE"] for r in rows)
    max_ms = max(r["max_ms"] for r in rows if r["arm"] == "candidate")
    checks = {
        "all_done": all_done, "max_call_under_1s": max_ms < 1000,
        "current_main_22_of_32": per_opponent["current_main"]["candidate"]["seed_block_points"] >= 22,
        "previous_main_22_of_32": per_opponent["previous_main"]["candidate"]["seed_block_points"] >= 22,
        "pooled_positive_95pct_lower_bound": interval[0] > 0,
        "public_v35_regression_at_most_4": per_opponent["public_v35"]["delta_seed_block_points"] >= -4,
        "public_c95_regression_at_most_4": per_opponent["public_c95"]["delta_seed_block_points"] >= -4,
    }
    summary = {"per_opponent": per_opponent, "pooled_win_rate_delta": sum(deltas) / len(deltas),
               "bootstrap_95pct_interval": interval, "max_candidate_ms": max_ms,
               "checks": checks, "gate_pass": all(checks.values())}
    result = {**manifest, "summary": summary, "seed_deltas": seed_deltas,
              "rows": sorted(rows, key=lambda r: (r["opponent"], r["seed"], r["seat"], r["arm"]))}
    (HERE / "reactive_panel.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
