from concurrent.futures import ProcessPoolExecutor, as_completed
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game
from diagnostics.shunki_mirror_quantity_20260927.confirm import summarize as quantity_summary

NEW = ROOT / "exp_shunki_disjoint_integrated_20260927.py"
RIVALS = {"a2": ROOT / "exp_shunki_market_queue_20260927.py",
          "1f": ROOT / "exp_shunki_visible_repair_20260927.py",
          "489": ROOT / "main_uploaded_mirror_straw24_20260926_489fe8e4.py",
          "C95": ROOT / "diagnostics/public_rayk_top_meta/public_c95_main.py"}


def branch(game):
    capture = game["candidate_capture"]
    seat = game["candidate_seat"]
    own, rival = capture["farms"][seat], capture["farms"][1-seat]
    farmice = capture["shops"][:2] == ["FARMERS_MARKET", "ICE_CREAM_SHOP"] and rival["counts"].get("MELON", 0) > 0
    mirror = own["land"] == rival["land"] and own["occupied"] == rival["occupied"]
    assert not (farmice and mirror)
    return "F" if farmice else "Q" if mirror else "A"


def actual_branch(game, component):
    telemetry = game.get("candidate_telemetry") or {}
    if component == "F":
        return "F" if telemetry.get("farmice_turns", 0) else "A"
    return "Q" if telemetry.get("mirror_quantity_active", False) else "A"


def key(row):
    return row["rival"], row["seed"], row["seat"]


def play(job):
    rival, seed, seat = job
    return {"key": list(job), "game": run_game(str(NEW), str(RIVALS[rival]), seed, seat, False, 144, {})}


def points(game):
    return 1 if game["margin"] > 0 else .5 if game["margin"] == 0 else 0


if __name__ == "__main__":
    manifest = json.loads((HERE / "manifest.json").read_text())
    assert hashlib.sha256(NEW.read_bytes()).hexdigest() == manifest["candidate_sha256"]
    paths = {"F": ROOT / "diagnostics/shunki_farmice_observed_20260927/confirmation.json",
             "Q": ROOT / "diagnostics/shunki_mirror_quantity_20260927/results.json"}
    components = {k: json.loads(p.read_text()) for k, p in paths.items()}
    assert all(c["complete"] and c["passed"] for c in components.values())
    panels = json.loads((ROOT / "diagnostics/shunki_farmice_observed_20260927/panels.json").read_text())
    anchors, mismatches = {}, []
    for name, data in components.items():
        for row in data["rows"]:
            if row["role"] != "new":
                continue
            observed = branch(row["game"])
            if observed != actual_branch(row["game"], name):
                mismatches.append({"component_panel": name, "key": list(key(row)), "old_branch": actual_branch(row["game"], name), "combined_branch": observed})
            is_anchor = (name == "F" and row["rival"] in ("489", "C95") and row["seed"] in [r["seed"] for r in panels[row["rival"]]][:2]) or (name == "Q" and row["rival"] in ("a2", "1f") and row["seed"] in (2690000, 2690001))
            if is_anchor:
                assert observed == actual_branch(row["game"], name)
                anchors[key(row)] = row["game"]
    assert len(anchors) == 16
    jobs = sorted(set(anchors) | {tuple(m["key"]) for m in mismatches})
    report = {"candidate_sha256": manifest["candidate_sha256"], "anchor_count": 16,
              "mismatches": mismatches, "planned_new_games": len(jobs), "rows": [], "complete": False, "passed": False}
    (HERE / "verification_plan.json").write_text(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2), encoding="utf8")
    with ProcessPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(play, job) for job in jobs]):
            row = future.result(); report["rows"].append(row)
            (HERE / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf8")
            print(len(report["rows"]), "/", len(jobs), row["key"], row["game"]["margin"], flush=True)
    by = {tuple(r["key"]): r["game"] for r in report["rows"]}
    parity = all(all(by[k][field] == expected[field] for field in ("candidate_reward", "opponent_reward")) for k, expected in anchors.items())
    all_done = all(r["game"]["candidate_status"] == r["game"]["opponent_status"] == "DONE" for r in report["rows"])
    errors = sum((r["game"].get("candidate_telemetry") or {}).get(field, 0) for r in report["rows"] for field in ("queue_errors", "quantity_errors", "mirror_quantity_errors", "farmice_errors", "integration_gate_collisions"))
    cohorts = {}
    for name, data in components.items():
        rows = copy.deepcopy(data["rows"])
        for row in rows:
            if row["role"] == "new":
                if key(row) in by:
                    row["game"] = by[key(row)]; row["measurement"] = "new combined game"
                else:
                    assert branch(row["game"]) == actual_branch(row["game"], name)
                    row["measurement"] = "reused identical component branch"
            else:
                row["measurement"] = "unchanged a2 control"
        cohorts[name] = rows
    qsummary = quantity_summary(cohorts["Q"])
    fscores = {rival: {role: sum(points(r["game"]) for r in cohorts["F"] if r["rival"] == rival and r["role"] == role) for role in ("old", "new")} for rival in ("489", "C95", "a2")}
    fnonregression = all(v["new"] >= v["old"] for v in fscores.values())
    report.update(complete=True, passed=parity and all_done and errors == 0 and qsummary["passed"] and fnonregression,
                  anchor_cash_parity=parity, all_done=all_done, errors=errors, quantity_panel=qsummary,
                  farmice_panel_scores=fscores, farmice_panel_win_nonregression=fnonregression)
    (HERE / "combined_native_cohorts.json").write_text(json.dumps({"candidate_sha256": manifest["candidate_sha256"], "cohorts": cohorts}, indent=2), encoding="utf8")
    (HERE / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf8")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}), flush=True)
