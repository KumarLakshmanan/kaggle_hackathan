from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PRIOR = ROOT / "diagnostics/shunki_route_search_20260927"
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def play(job):
    route, seat = job
    r = run_game(str(ROOT / "exp_shunki_shop_pruned_20260927.py"), "rawroute:" + route["path"],
                 route["seed"], seat, False, 144, {})
    return {"team": route["team"], "seed": route["seed"], "seat": seat, "margin": r["margin"],
            "statuses": [r["candidate_status"], r["opponent_status"]],
            "shops": r["candidate_capture"]["shops"], "telemetry": r["candidate_telemetry"]}


if __name__ == "__main__":
    source = ROOT / "exp_shunki_shop_optimized_20260927.py"
    assert sha(source) == "94f0602f0a6a2d4c1af84f8caf93ee802335582485dd2f796a8c7e5a09846604"
    raw = source.read_bytes() + b'''\n\n# Rejected native bakery replacement removed; all other policy paths identical.\n_OPT_TABLE.pop("BAKERY|PET_CAFE")\n\ndef kaggle_shop_pruned_entrypoint(observation, configuration=None):\n    return agent(observation, configuration)\n'''
    candidate = ROOT / "exp_shunki_shop_pruned_20260927.py"
    compile(raw, str(candidate), "exec")
    candidate.write_bytes(raw)
    old_manifest = json.loads((PRIOR / "candidate_manifest.json").read_text(encoding="utf8"))
    table = {k: v for k, v in old_manifest["selected"].items() if k != "BAKERY|PET_CAFE"}
    manifest = {"candidate": str(candidate), "candidate_sha256": sha(candidate),
                "source_sha256": old_manifest["source_sha256"], "construction_parent_sha256": sha(source),
                "selected": table, "change": "Remove only BAKERY|PET_CAFE override", "plan_sha256": sha(HERE / "PLAN.md")}
    (HERE / "candidate_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    routes = json.loads((ROOT / "diagnostics/top50_refresh_20260927_2303/routes/summary.json").read_text(encoding="utf8"))
    cases = [r for r in routes if r["team"] in ("Snorlax", "We wanna be tomatos")]
    with ProcessPoolExecutor(max_workers=2) as pool:
        games = list(pool.map(play, [(r, s) for r in cases for s in (0, 1)]))
    old_decision = json.loads((PRIOR / "top50_decision.json").read_text(encoding="utf8"))
    rows = old_decision["rows"]
    for row in rows:
        changed = [g for g in games if g["team"] == row["team"]]
        row["measurement"] = "prior 94f: unchanged branch" if not changed else "new pruned run"
        if changed:
            assert len(changed) == 2
            changed.sort(key=lambda g: g["seat"])
            assert all(g["shops"][:2] == ["BAKERY", "PET_CAFE"] and g["telemetry"]["optimized_turns"] == 0 for g in changed)
            row["new_margins"] = [g["margin"] for g in changed]
            assert row["new_margins"] == row["old_margins"], "Removed branch must reproduce submitted parent"
            row["new_sweep"] = all(g["margin"] > 0 for g in changed)
            row["all_done"] = all(g["statuses"] == ["DONE", "DONE"] for g in changed)
    summary = {"old_sweeps": sum(r["old_sweep"] for r in rows), "new_sweeps": sum(r["new_sweep"] for r in rows),
               "seat_wins": sum(m > 0 for r in rows for m in r["new_margins"]),
               "all_done": all(r["all_done"] for r in rows), "new_games": 4, "reused_unchanged_games": 96}
    summary["gate_pass"] = summary["all_done"] and summary["new_sweeps"] > summary["old_sweeps"] and not any(r["old_sweep"] and not r["new_sweep"] for r in rows)
    result = {"candidate_sha256": sha(candidate), "summary": summary, "prior_result_sha256": sha(PRIOR / "top50_decision.json"),
              "proof": "Only fixed first-two-shop BAKERY/PET branch differs; 48 other openings and full policies unchanged", "new_games": games, "rows": rows}
    (HERE / "top50_decision.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf8")
    print(json.dumps({"candidate_sha256": sha(candidate), "summary": summary}, indent=2), flush=True)
