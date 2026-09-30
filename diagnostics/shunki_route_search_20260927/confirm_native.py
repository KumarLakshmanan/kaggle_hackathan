"""Frozen, outcome-blind branch coverage followed by reactive native games."""
from concurrent.futures import ProcessPoolExecutor, as_completed
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "native"
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module, make, run_game, engine_version

OLD = ROOT / "main_uploaded_shunki_schedule_20260927_3cc0f69f.py"
NEW = ROOT / "exp_shunki_shop_optimized_20260927.py"
PREFIX_PATH = ROOT / "diagnostics/shunki_ice_schedule_20260927/scan_prefixes.json"
PREFIXES = json.loads(PREFIX_PATH.read_text(encoding="utf8"))
RIVALS = {
    "old489": (ROOT / "main_uploaded_mirror_straw24_20260926_489fe8e4.py", 2634800),
    "old08aa": (ROOT / "main_uploaded_entrypoint_fix_20260926_08aa268a.py", 2637000),
    "public_c95": (ROOT / "diagnostics/public_rayk_top_meta/public_c95_main.py", 2639200),
    "submitted3cc": (OLD, 2641400),
}
BRANCHES = ["BAKERY|PET_CAFE", "FARMERS_MARKET|ICE_CREAM_SHOP",
            "PIZZA_SHOP|ICE_CREAM_SHOP", "YARN_STORE|PET_CAFE"]
MAX_SCAN, NEEDED, WORKERS = 2048, 8, 4


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf8")


def first_shops(job):
    rival, seed = job
    module = _load_module(RIVALS[rival][0], "schedule_scan")
    try:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        trainer = env.train([None, module.agent])
        obs = trainer.reset()
        for step in range(144):
            shops = obs["town"]["unlocked_shops"]
            tape = PREFIXES[shops[0]] if step >= 72 and shops else next(iter(PREFIXES.values()))
            obs, _, done, _ = trainer.step(copy.deepcopy(tape[step]))
            assert not done, (rival, seed, step)
        return {"rival": rival, "seed": seed, "shops": list(obs["town"]["unlocked_shops"][:2])}
    finally:
        sys.modules.pop(module.__name__, None)


def play(job):
    arm, rival, seed, seat, selected_branch = job
    result = run_game(str(NEW if arm == "new" else OLD), str(RIVALS[rival][0]),
                      seed, seat, False, 144, {})
    margin = result["margin"]
    return {"arm": arm, "rival": rival, "seed": seed, "seat": seat,
            "selected_branch": selected_branch,
            "shops": result["candidate_capture"]["shops"][:2],
            "own_cash": result["candidate_reward"], "rival_cash": result["opponent_reward"],
            "margin": margin, "points": 1.0 if margin > 0 else 0.5 if margin == 0 else 0.0,
            "statuses": [result["candidate_status"], result["opponent_status"]],
            "telemetry": result["candidate_telemetry"], "max_ms": result["candidate_timing"]["max_ms"]}


def selected_rows(scanned):
    return {branch: [row for row in scanned if "|".join(row["shops"]) == branch][:NEEDED]
            for branch in BRANCHES}


def summarize(rows, panels):
    by = {(r["arm"], r["rival"], r["seed"], r["seat"]): r for r in rows}
    details, paired = {}, []
    for rival, panel in panels.items():
        arms = ("new",) if rival == "submitted3cc" else ("old", "new")
        detail = {arm: {} for arm in arms}
        for arm in arms:
            games = [r for r in rows if r["rival"] == rival and r["arm"] == arm]
            detail[arm] = {"seat_games": len(games), "wins": sum(r["margin"] > 0 for r in games),
                           "draws": sum(r["margin"] == 0 for r in games),
                           "paired_points": sum(r["points"] for r in games) / 2,
                           "activated_by_seat": {str(s): sum(bool((r["telemetry"] or {}).get("optimized_turns"))
                               for r in games if r["seat"] == s) for s in (0, 1)},
                           "branches": {branch: {"seat_games": sum(r["selected_branch"] == branch for r in games),
                               "paired_points": sum(r["points"] for r in games if r["selected_branch"] == branch) / 2}
                               for branch in BRANCHES}}
        details[rival] = detail
        for branch, selected in panel.items():
            for scan in selected:
                seed = scan["seed"]
                item = {"rival": rival, "seed": seed, "selected_branch": branch}
                for arm in arms:
                    pair = [by[arm, rival, seed, seat] for seat in (0, 1)]
                    item[arm + "_points"] = sum(r["points"] for r in pair) / 2
                    item[arm + "_margins"] = [r["margin"] for r in pair]
                if "old" in arms:
                    item["opening_shop_parity"] = all(by["old", rival, seed, seat]["shops"] ==
                                                       by["new", rival, seed, seat]["shops"] for seat in (0, 1))
                paired.append(item)
    external = [key for key in RIVALS if key != "submitted3cc"]
    checks = {
        "all_448_games": len(rows) == 448,
        "all_done": all(r["statuses"] == ["DONE", "DONE"] for r in rows),
        "complete_branch_coverage": all(len(panel[branch]) == NEEDED for panel in panels.values() for branch in BRANCHES),
        "opening_shop_parity": all(r.get("opening_shop_parity", True) for r in paired),
        "pooled_external_no_regression": sum(details[k]["new"]["paired_points"] for k in external) >=
                                          sum(details[k]["old"]["paired_points"] for k in external),
        "no_external_rival_loses_over_two_points": all(details[k]["new"]["paired_points"] >=
                                                       details[k]["old"]["paired_points"] - 2 for k in external),
        "head_to_head_at_least_20_of_32": details["submitted3cc"]["new"]["paired_points"] >= 20,
    }
    return {"candidate_sha256": sha(NEW), "summary": details, "checks": checks,
            "gate_pass": all(checks.values()), "paired": paired, "rows": rows}


def main():
    OUT.mkdir(exist_ok=True)
    candidate = json.loads((HERE / "candidate_manifest.json").read_text(encoding="utf8"))
    assert sha(NEW) == candidate["candidate_sha256"]
    assert sha(OLD) == candidate["source_sha256"]
    assert json.loads((HERE / "top50_decision.json").read_text(encoding="utf8"))["summary"]["gate_pass"]
    # Check every optimized scan action against both actual policy callables.
    # No environment or future result is involved in this byte parity check.
    prefix_checks = {}
    for path in (OLD, NEW):
        module = _load_module(path, "prefix_parity")
        try:
            for shop, tape in PREFIXES.items():
                assert all(module.agent({"step": step, "town": {"unlocked_shops": [] if step < 72 else [shop]}})
                           == tape[step] for step in range(144)), (path, shop)
            prefix_checks[path.name] = "all 8 first-shop prefixes, all 144 actions exact"
        finally:
            sys.modules.pop(module.__name__, None)
    fixed = {"candidate_sha256": sha(NEW), "baseline_sha256": sha(OLD),
             "opponents": {k: {"path": str(p), "sha256": sha(p), "scan_start": start}
                           for k, (p, start) in RIVALS.items()},
             "plan_sha256": sha(HERE / "PLAN.md"), "runner_sha256": sha(Path(__file__)),
             "prefix_sha256": sha(PREFIX_PATH), "engine_version": engine_version,
             "branches": BRANCHES, "needed_per_branch": NEEDED, "max_scan_per_rival": MAX_SCAN,
             "prefix_parity": prefix_checks, "workers": WORKERS}
    manifest_path = OUT / "manifest.json"
    if manifest_path.exists():
        prior = json.loads(manifest_path.read_text(encoding="utf8"))
        assert prior["fixed"] == fixed, "Frozen inputs changed; refuse resume"
    else:
        save("manifest.json", {"started_utc": datetime.now(timezone.utc).isoformat(), "fixed": fixed})
    panels = {}
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        for rival, (_, start_seed) in RIVALS.items():
            selection_path = OUT / (rival + "_selection.json")
            scanned = json.loads(selection_path.read_text(encoding="utf8"))["scanned"] if selection_path.exists() else []
            assert [r["seed"] for r in scanned] == list(range(start_seed, start_seed + len(scanned)))
            panel = selected_rows(scanned)
            while min(map(len, panel.values())) < NEEDED and len(scanned) < MAX_SCAN:
                start = start_seed + len(scanned)
                jobs = [(rival, seed) for seed in range(start, min(start + 32, start_seed + MAX_SCAN))]
                scanned.extend(pool.map(first_shops, jobs))
                panel = selected_rows(scanned)
                save(rival + "_selection.json", {"selected": panel, "scanned": scanned})
                print(rival, "scanned", len(scanned), "coverage", {k: len(v) for k, v in panel.items()}, flush=True)
            if min(map(len, panel.values())) < NEEDED:
                save("coverage_failure.json", {"rival": rival, "coverage": {k: len(v) for k, v in panel.items()},
                                               "gate_pass": False})
                print("Selection limit exhausted; no confirmation pass.", flush=True)
                return
            panels[rival] = panel
    save("panels.json", panels)
    jobs = [(arm, rival, row["seed"], seat, branch)
            for rival, panel in panels.items()
            for arm in (("new",) if rival == "submitted3cc" else ("old", "new"))
            for branch, selected in panel.items() for row in selected for seat in (0, 1)]
    partial = OUT / "confirmation_partial.json"
    rows = json.loads(partial.read_text(encoding="utf8"))["rows"] if partial.exists() else []
    completed = {(r["arm"], r["rival"], r["seed"], r["seat"], r["selected_branch"]) for r in rows}
    assert len(completed) == len(rows) and completed <= set(jobs)
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        for future in as_completed([pool.submit(play, job) for job in jobs if job not in completed]):
            rows.append(future.result())
            if len(rows) % 8 == 0:
                save("confirmation_partial.json", {"rows": rows})
                print("reactive confirmation", len(rows), "/", len(jobs), flush=True)
    result = summarize(rows, panels)
    save("confirmation.json", result)
    print(json.dumps({k: v for k, v in result.items() if k not in ("paired", "rows")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
