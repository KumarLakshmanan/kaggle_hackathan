"""Outcome-blind native shop selection, then independent branch validation."""
from concurrent.futures import ProcessPoolExecutor, as_completed
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module, make, run_game

MAIN = ROOT / "main.py"
OLD = ROOT / "exp_shunki_later_lookup_20260927.py"
NEW = ROOT / "exp_shunki_ice_schedule_20260927.py"
PREVIOUS = ROOT / "main_uploaded_entrypoint_fix_20260926_08aa268a.py"
PREFIXES = json.loads((HERE / "scan_prefixes.json").read_text(encoding="utf8"))
START, MAX_SCAN, NEEDED = 2632000, 1024, 8
TARGET = ["ICE_CREAM_SHOP", "BRUNCH_SPOT"]


def first_shops(seed):
    module = _load_module(MAIN, "ice_scan")
    try:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        trainer = env.train([None, module.agent])
        obs = trainer.reset()
        for step in range(144):
            shops = obs["town"]["unlocked_shops"]
            tape = PREFIXES[shops[0]] if step >= 72 and shops else next(iter(PREFIXES.values()))
            obs, _, done, _ = trainer.step(copy.deepcopy(tape[step]))
            assert not done
        return {"seed": seed, "shops": list(obs["town"]["unlocked_shops"][:2])}
    finally:
        sys.modules.pop(module.__name__, None)


def play(job):
    arm, opponent, seed, seat = job
    own = {"original": OLD, "new": NEW, "main_control": MAIN}[arm]
    rival = MAIN if opponent == "current_main" else PREVIOUS
    r = run_game(str(own), str(rival), seed, seat, False, 216, {})
    margin = r["margin"]
    return {"arm": arm, "opponent": opponent, "seed": seed, "seat": seat,
            "own_cash": r["candidate_reward"], "rival_cash": r["opponent_reward"], "margin": margin,
            "points": 1.0 if margin > 0 else 0.5 if margin == 0 else 0.0,
            "statuses": [r["candidate_status"], r["opponent_status"]],
            "shops": r["candidate_capture"]["shops"][:3], "max_ms": r["candidate_timing"]["max_ms"]}


def main():
    build = json.loads((HERE / "build_manifest.json").read_text(encoding="utf8"))
    assert hashlib.sha256(NEW.read_bytes()).hexdigest() == build["candidate_sha256"]
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
    assert json.loads((HERE / "development.json").read_text(encoding="utf8"))["summary"]["gate_pass"]
    # Confirm the optimized prefix scanner reproduces an already measured
    # native seed before using it to select any unobserved confirmation seed.
    known = json.loads((ROOT / "diagnostics/winrate_review_20260927/partial.json").read_text(encoding="utf8"))["rows"]
    expected = next(r["shops"] for r in known if r["arm"] == "candidate" and r["opponent"] == "current_main" and r["seed"] == 2631000 and r["seat"] == 0)
    parity = first_shops(2631000)
    assert parity["shops"] == expected, (parity, expected)
    scanned, selected = [], []
    with ProcessPoolExecutor(max_workers=2) as pool:
        for start in range(START, START + MAX_SCAN, 32):
            scanned.extend(pool.map(first_shops, range(start, min(start + 32, START + MAX_SCAN))))
            selected = [r["seed"] for r in scanned if r["shops"] == TARGET][:NEEDED]
            (HERE / "seed_selection.json").write_text(json.dumps({"start": START, "max_scan": MAX_SCAN,
                                                                  "target": TARGET, "selected": selected,
                                                                  "prefix_parity": parity, "scanned": scanned}, indent=2), encoding="utf8")
            print(f"shop scans {len(scanned)}, selected {len(selected)}/{NEEDED}", flush=True)
            if len(selected) == NEEDED:
                break
    if len(selected) != NEEDED:
        print("Insufficient qualifying seeds in frozen scan budget; no confirmation claim.", flush=True)
        return
    jobs = [(arm, opp, seed, seat) for opp in ("current_main", "previous_main")
            for arm in (("original", "new", "main_control") if opp == "current_main" else ("original", "new"))
            for seed in selected for seat in (0, 1)]
    rows = []
    with ProcessPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(play, job) for job in jobs]):
            rows.append(future.result())
            if len(rows) % 8 == 0:
                (HERE / "confirmation_partial.json").write_text(json.dumps({"rows": rows}, indent=2), encoding="utf8")
                print(f"confirmation {len(rows)}/{len(jobs)}", flush=True)
    by = {(r["arm"], r["opponent"], r["seed"], r["seat"]): r for r in rows}
    summary, paired = {}, []
    for opp in ("current_main", "previous_main"):
        detail = {}
        for arm in ("original", "new"):
            games = [r for r in rows if r["arm"] == arm and r["opponent"] == opp]
            detail[arm + "_seed_block_points"] = sum(r["points"] for r in games) / 2
        for seed in selected:
            old = [by[("original", opp, seed, s)] for s in (0, 1)]
            new = [by[("new", opp, seed, s)] for s in (0, 1)]
            paired.append({"opponent": opp, "seed": seed,
                           "old_points": sum(r["points"] for r in old) / 2,
                           "new_points": sum(r["points"] for r in new) / 2,
                           "delta_own": sum(b["own_cash"] - a["own_cash"] for a, b in zip(old, new)),
                           "delta_margin": sum(b["margin"] - a["margin"] for a, b in zip(old, new)),
                           "same_first_three_shops": all(a["shops"] == b["shops"] for a, b in zip(old, new)),
                           "exposed_seats": sum(r["shops"][:2] == TARGET and len(r["shops"]) >= 3 and r["shops"][2] not in ("YARN_STORE", "PIZZA_SHOP") for r in old)})
        summary[opp] = detail
    exposed = sum(r["exposed_seats"] == 2 for r in paired if r["opponent"] == "current_main")
    checks = {"all_done": all(r["statuses"] == ["DONE", "DONE"] for r in rows),
              "six_of_eight_against_each": all(v["new_seed_block_points"] >= 6 for v in summary.values()),
              "no_opponent_win_regression": all(v["new_seed_block_points"] >= v["original_seed_block_points"] for v in summary.values()),
              "at_least_one_added_win_point": sum(v["new_seed_block_points"] - v["original_seed_block_points"] for v in summary.values()) >= 1,
              "no_new_double_loss": not any(r["old_points"] == 1 and r["new_points"] == 0 for r in paired),
              "at_least_four_exposed_pairs": exposed >= 4}
    result = {"candidate_sha256": build["candidate_sha256"], "selected": selected, "summary": summary,
              "exposed_current_main_pairs": exposed, "checks": checks, "gate_pass": all(checks.values()),
              "paired": paired, "rows": rows}
    (HERE / "confirmation.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("paired", "rows")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
