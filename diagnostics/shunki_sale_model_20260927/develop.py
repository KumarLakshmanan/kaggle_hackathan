from concurrent.futures import ProcessPoolExecutor
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
    r = run_game(str(ROOT / "exp_shunki_sale_model_20260927.py"), "rawroute:" + route["path"],
                 route["seed"], seat, False, 144, {})
    return {"team": route["team"], "seed": route["seed"], "seat": seat, "baseline_margin": baseline,
            "margin": r["margin"], "statuses": [r["candidate_status"], r["opponent_status"]],
            "telemetry": r["candidate_telemetry"], "max_ms": r["candidate_timing"]["max_ms"]}


if __name__ == "__main__":
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf8"))
    assert hashlib.sha256(Path(manifest["candidate"]).read_bytes()).hexdigest() == manifest["candidate_sha256"]
    routes = json.loads((ROOT / "diagnostics/top50_refresh_20260927_2303/routes/summary.json").read_text(encoding="utf8"))
    baseline = json.loads((ROOT / "diagnostics/shunki_route_search_20260927/top50_decision.json").read_text(encoding="utf8"))["rows"]
    cases = [row for row in baseline if not row["new_sweep"]]
    jobs = [(next(r for r in routes if r["team"] == case["team"]), seat, case["new_margins"][seat])
            for case in cases for seat in (0, 1)]
    with ProcessPoolExecutor(max_workers=1) as pool:
        rows = list(pool.map(play, jobs))
    new_sweeps = sum(all(r["margin"] > 0 for r in rows if r["team"] == case["team"]) for case in cases)
    checks = {"strict_sweep_increase": new_sweeps > 0,
              "no_won_seat_lost": all(r["margin"] > 0 for r in rows if r["baseline_margin"] > 0),
              "all_done": all(r["statuses"] == ["DONE", "DONE"] for r in rows),
              "changes_active": all(r["telemetry"].get("advanced_units", 0) > 0 for r in rows)}
    result = {"candidate_sha256": manifest["candidate_sha256"], "checks": checks,
              "gate_pass": all(checks.values()), "new_sweeps": new_sweeps, "rows": rows}
    (HERE / "development.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf8")
    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)
