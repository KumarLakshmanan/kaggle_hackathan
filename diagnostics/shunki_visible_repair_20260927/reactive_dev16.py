"""Fresh native three-arm comparison for the Shunki visible-worker repair."""

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
BASE = ROOT / "exp_shunki_later_lookup_20260927.py"
CANDIDATE = ROOT / "exp_shunki_visible_repair_20260927.py"
MAIN_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
BASE_HASH = "68aad0908c38884aba856373088f1a6ba4a0423df2ee00edbec4c796f8e45fac"
CANDIDATE_HASH = "1f22192297821ab5205b8cdcbd22bd1fab30d546860f3c61e8096a2a4355446b"
SEEDS = tuple(range(2630400, 2630416))


def play(job):
    arm, seed, seat = job
    path = {"main": MAIN, "base": BASE, "repair": CANDIDATE}[arm]
    game = run_game(str(path), str(MAIN), seed, seat, False, 144, {})
    return {"arm": arm, "seed": seed, "seat": seat,
            "own_cash": game["candidate_reward"], "rival_cash": game["opponent_reward"],
            "margin": game["margin"], "statuses": [game["candidate_status"], game["opponent_status"]],
            "shops": game["candidate_capture"]["shops"][:2],
            "telemetry": game["candidate_telemetry"],
            "max_candidate_ms": game["candidate_timing"]["max_ms"]}


def main():
    for path, expected in ((MAIN, MAIN_HASH), (BASE, BASE_HASH), (CANDIDATE, CANDIDATE_HASH)):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path
    assert (HERE / "candidate_parity.json").is_file()
    jobs = [(arm, seed, seat) for arm in ("main", "base", "repair")
            for seed in SEEDS for seat in (0, 1)]
    rows = []
    with ProcessPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(play, job): job for job in jobs}
        for future in as_completed(futures):
            rows.append(future.result())
            if len(rows) % 12 == 0:
                (HERE / "dev_partial.json").write_text(
                    json.dumps({"completed": len(rows), "rows": rows}, indent=2), encoding="utf8")
                print(f"completed {len(rows)}/{len(jobs)}", flush=True)
    by = {(row["arm"], row["seed"], row["seat"]): row for row in rows}
    comparisons = []
    paired = []
    for seed in SEEDS:
        seat_rows = []
        for seat in (0, 1):
            control = by[("main", seed, seat)]
            base = by[("base", seed, seat)]
            trial = by[("repair", seed, seat)]
            stats = trial["telemetry"] or {}
            trigger_count = int(stats.get("idle_weed_digs", 0)) + int(stats.get("blocked_work_digs", 0))
            result = {"seed": seed, "seat": seat, "triggers": trigger_count,
                      "repair_stats": stats,
                      "delta_repair_vs_base_own": trial["own_cash"] - base["own_cash"],
                      "delta_repair_vs_base_rival": trial["rival_cash"] - base["rival_cash"],
                      "delta_repair_vs_base_margin": trial["margin"] - base["margin"],
                      "delta_repair_vs_main_own": trial["own_cash"] - control["own_cash"],
                      "delta_repair_vs_main_margin": trial["margin"] - control["margin"],
                      "shops_main": control["shops"], "shops_repair": trial["shops"],
                      "statuses": trial["statuses"]}
            comparisons.append(result)
            seat_rows.append(result)
        paired.append({"seed": seed,
                       "triggers": sum(row["triggers"] for row in seat_rows),
                       "base_own_delta": sum(row["delta_repair_vs_base_own"] for row in seat_rows),
                       "base_rival_delta": sum(row["delta_repair_vs_base_rival"] for row in seat_rows),
                       "base_margin_delta": sum(row["delta_repair_vs_base_margin"] for row in seat_rows),
                       "main_own_delta": sum(row["delta_repair_vs_main_own"] for row in seat_rows),
                       "main_margin_delta": sum(row["delta_repair_vs_main_margin"] for row in seat_rows)})
    active = [row for row in paired if row["triggers"] > 0]
    all_done = all(row["statuses"] == ["DONE", "DONE"] for row in rows)
    parity = sum(row["shops_main"] == row["shops_repair"] for row in comparisons)
    summary = {"all_done": all_done, "shop_parity_seats": parity,
               "activated_seeds": len(active), "positive_active_vs_base": sum(row["base_margin_delta"] > 0 for row in active),
               "total_active_vs_base_own": sum(row["base_own_delta"] for row in active),
               "total_active_vs_base_margin": sum(row["base_margin_delta"] for row in active),
               "worst_active_vs_base_margin": min((row["base_margin_delta"] for row in active), default=None),
               "positive_pairs_vs_main": sum(row["main_margin_delta"] > 0 for row in paired),
               "total_vs_main_own": sum(row["main_own_delta"] for row in paired),
               "total_vs_main_margin": sum(row["main_margin_delta"] for row in paired),
               "worst_vs_main_margin": min(row["main_margin_delta"] for row in paired),
               "total_repair_errors": sum((row["telemetry"] or {}).get("repair_errors", 0)
                                          for row in rows if row["arm"] == "repair")}
    gate = (all_done and parity >= 30 and len(active) >= 3
            and summary["total_active_vs_base_own"] > 0
            and summary["total_active_vs_base_margin"] > 0
            and summary["worst_active_vs_base_margin"] >= -5000
            and summary["positive_pairs_vs_main"] >= 12
            and summary["total_vs_main_own"] > 0
            and summary["worst_vs_main_margin"] >= -10000
            and summary["total_repair_errors"] == 0)
    summary["gate_pass"] = gate
    result = {"main_sha256": MAIN_HASH, "base_sha256": BASE_HASH,
              "candidate_sha256": CANDIDATE_HASH, "seeds": SEEDS,
              "summary": summary, "paired": paired, "comparisons": comparisons,
              "rows": sorted(rows, key=lambda row: (row["arm"], row["seed"], row["seat"]))}
    (HERE / "reactive_dev16.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    for row in paired:
        print(row, flush=True)
    print(summary, flush=True)


if __name__ == "__main__":
    main()
