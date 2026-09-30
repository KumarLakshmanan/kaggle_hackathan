"""Prospective native gates; stop once a mandatory phase fails."""
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game

NEW = ROOT/"exp_shunki_market_queue_20260927.py"
OLD = ROOT/"main_uploaded_shunki_schedule_20260927_3cc0f69f.py"
ACTIVE = ROOT/"exp_shunki_visible_repair_20260927.py"
RIVALS = {
    "489": ROOT/"main_uploaded_mirror_straw24_20260926_489fe8e4.py",
    "C95": ROOT/"diagnostics/public_rayk_top_meta/public_c95_main.py",
}
SEEDS = list(range(2660000, 2660032))


def point(game):
    return 1. if game["margin"] > 0 else .5 if game["margin"] == 0 else 0.


def game(job):
    phase, role, opponent, seed, seat = job
    r = run_game(str(NEW if role == "new" else OLD), str(opponent), seed, seat, False, 144, {})
    return {"phase": phase, "role": role, "seed": seed, "seat": seat, "game": r}


if __name__ == "__main__":
    manifest = json.loads((HERE/"manifest.json").read_text())
    assert hashlib.sha256(NEW.read_bytes()).hexdigest() == manifest["candidate_sha256"]
    panel = json.loads((HERE/"top50.json").read_text(encoding="utf8"))
    baseline = json.loads((ROOT/"diagnostics/top50_refresh_20260927_2303/candidate_top50.json").read_text(encoding="utf8"))
    before = {r["team"]: all(g["margin"] > 0 for g in r["games"]) for r in baseline["rows"]}
    sweeps = sum(all(g["margin"] > 0 for g in r["games"]) for r in panel["rows"])
    lost = sum(before[r["team"]] and not all(g["margin"] > 0 for g in r["games"]) for r in panel["rows"])
    assert sweeps > 42 and lost <= 1 and panel["summary"]["all_done"], (sweeps, lost)
    records = []
    report = {"candidate_sha256": manifest["candidate_sha256"], "plan_sha256": manifest["plan_sha256"],
              "seeds": SEEDS, "phase_order": ["head_main", "head_best_active", "external"],
              "maximum_games_if_all_phases_pass": 384, "completed_phases": [], "rows": records}
    paths = {"new": NEW, "old": OLD, "best_active": ACTIVE, **RIVALS}
    report["artifacts"] = {k: {"path": str(v), "sha256": hashlib.sha256(v.read_bytes()).hexdigest()} for k,v in paths.items()}
    for phase, opponent in (("head_main", OLD), ("head_best_active", ACTIVE), ("external", None)):
        jobs = [(phase, "new", opponent, seed, seat) for seed in SEEDS for seat in (0, 1)] if opponent else [
            (phase+":"+name, role, rival, seed, seat)
            for name,rival in RIVALS.items() for seed in SEEDS for role in ("old", "new") for seat in (0, 1)]
        block = []
        with ProcessPoolExecutor(max_workers=4) as pool:
            for f in as_completed([pool.submit(game, job) for job in jobs]):
                r = f.result()
                records.append(r)
                block.append(r)
                (HERE/"confirmation.json").write_text(json.dumps(report, indent=2), encoding="utf8")
                print(phase, len(block), "/", len(jobs), r["role"], r["seed"], r["seat"], r["game"]["margin"], flush=True)
        done = all(r["game"]["candidate_status"] == r["game"]["opponent_status"] == "DONE" for r in block)
        errors = sum((r["game"].get("candidate_telemetry") or {}).get("queue_errors", 0) for r in block)
        done = done and errors == 0
        if opponent:
            points = sum(point(r["game"]) for r in block)/2
            required = 20 if phase == "head_main" else 16
            gate = {"phase": phase, "games": len(block), "all_done": done, "paired_points": points, "required": required, "passed": done and points >= required}
        else:
            scores = {name: {role: sum(point(r["game"]) for r in block if r["phase"] == "external:"+name and r["role"] == role)
                             for role in ("old", "new")} for name in RIVALS}
            passed = done and all(v["new"] >= v["old"] for v in scores.values()) and sum(v["new"]-v["old"] for v in scores.values()) > 0
            gate = {"phase": phase, "games": len(block), "all_done": done, "scores": scores, "passed": passed}
        gate["queue_errors"] = errors
        report["completed_phases"].append(gate)
        report["passed"] = gate["passed"]
        (HERE/"confirmation.json").write_text(json.dumps(report, indent=2), encoding="utf8")
        print("GATE", json.dumps(gate), flush=True)
        if not gate["passed"]:
            break
