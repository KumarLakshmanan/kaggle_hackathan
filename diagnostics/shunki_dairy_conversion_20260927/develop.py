from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game


def play(job):
    route, seat, baseline = job
    r = run_game(str(ROOT / "exp_shunki_dairy_conversion_20260927.py"), "rawroute:" + route["path"],
                 route["seed"], seat, False, 144, {})
    return {"team": route["team"], "seed": route["seed"], "seat": seat, "baseline_margin": baseline,
            "margin": r["margin"], "statuses": [r["candidate_status"], r["opponent_status"]],
            "telemetry": r["candidate_telemetry"], "shops": r["candidate_capture"]["shops"]}


if __name__ == "__main__":
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf8"))
    assert hashlib.sha256(Path(manifest["candidate"]).read_bytes()).hexdigest() == manifest["candidate_sha256"]
    routes = json.loads((ROOT / "diagnostics/top50_refresh_20260927_2303/routes/summary.json").read_text(encoding="utf8"))
    baseline = json.loads((ROOT / "diagnostics/shunki_route_search_20260927/top50_decision.json").read_text(encoding="utf8"))["rows"]
    teams = ("Arda Ceylan", "Breaking1800", "ymg_aq")
    jobs = [(next(r for r in routes if r["team"] == team), seat,
             next(r for r in baseline if r["team"] == team)["new_margins"][seat]) for team in teams for seat in (0, 1)]
    with ProcessPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(play, jobs))
    old_sweeps = sum(all(r["baseline_margin"] > 0 for r in rows if r["team"] == team) for team in teams)
    new_sweeps = sum(all(r["margin"] > 0 for r in rows if r["team"] == team) for team in teams)
    checks = {"strict_sweep_increase": new_sweeps > old_sweeps,
              "no_won_seat_lost": all(r["margin"] > 0 for r in rows if r["baseline_margin"] > 0),
              "all_done": all(r["statuses"] == ["DONE", "DONE"] for r in rows),
              "coherent_changes_active": all(all(r["telemetry"].get(key, 0) > 0 for key in
                                                ("animal_orders", "animal_commands", "structures", "sale_orders")) for r in rows)}
    result = {"candidate_sha256": manifest["candidate_sha256"], "checks": checks,
              "gate_pass": all(checks.values()), "old_sweeps": old_sweeps, "new_sweeps": new_sweeps, "rows": rows}
    (HERE / "development.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps(result, indent=2), flush=True)
