from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module, make, run_game

NEW = ROOT / "exp_shunki_farmice_observed_20260927.py"
OLD = ROOT / "exp_shunki_market_queue_20260927.py"
RIVALS = {"489": (ROOT / "main_uploaded_mirror_straw24_20260926_489fe8e4.py", 2678000, 12),
          "C95": (ROOT / "diagnostics/public_rayk_top_meta/public_c95_main.py", 2680200, 12),
          "a2": (OLD, 2682400, 8)}


def save(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2), encoding="utf8")


def prefix(job):
    rival, seed = job
    own = _load_module(OLD, "farmice_scan_own")
    other = _load_module(RIVALS[rival][0], "farmice_scan_rival")
    try:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        trainer = env.train([None, other.agent])
        obs = trainer.reset()
        for step in range(144):
            obs, _, done, _ = trainer.step(own.agent(obs, env.configuration))
            assert not done
        shops = list(obs["town"]["unlocked_shops"][:2])
        melons = sum(isinstance(tile, dict) and tile.get("crop") == "MELON"
                     for row in obs["farms"][1]["tiles"] for tile in row)
        return {"rival": rival, "seed": seed, "shops": shops, "rival_melons": melons,
                "qualifies": shops == ["FARMERS_MARKET", "ICE_CREAM_SHOP"] and (rival == "a2" or melons > 0)}
    finally:
        sys.modules.pop(own.__name__, None)
        sys.modules.pop(other.__name__, None)


def play(job):
    rival, role, seed, seat = job
    return {"rival": rival, "role": role, "seed": seed, "seat": seat,
            "game": run_game(str(NEW if role == "new" else OLD), str(RIVALS[rival][0]), seed, seat, False, 144, {})}


def point(game):
    return 1 if game["margin"] > 0 else .5 if game["margin"] == 0 else 0


if __name__ == "__main__":
    assert hashlib.sha256(NEW.read_bytes()).hexdigest() == "f66be305e429a1b6de24ef79e8bd2255567d9589c5d69eb1a038cf833196b199"
    assert hashlib.sha256(OLD.read_bytes()).hexdigest() == "a2d2869c1d53bcfcedc8514d004f73bbab27ec6ef22b34d23241e718e4c1bf47"
    assert json.loads((HERE / "top50_decision.json").read_text())["passed"]
    fixed = {"candidate_sha256": hashlib.sha256(NEW.read_bytes()).hexdigest(),
             "plan_sha256": hashlib.sha256((HERE / "NATIVE_PLAN.md").read_bytes()).hexdigest(),
             "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             "references": {k: {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "start": start, "needed": n}
                            for k, (p, start, n) in RIVALS.items()}}
    save("native_manifest.json", fixed)
    panels = {}
    with ProcessPoolExecutor(max_workers=4) as pool:
        for rival, (_, start, needed) in RIVALS.items():
            scanned = []
            while len([r for r in scanned if r["qualifies"]]) < needed and len(scanned) < 2048:
                jobs = [(rival, seed) for seed in range(start+len(scanned), start+min(len(scanned)+32, 2048))]
                scanned.extend(pool.map(prefix, jobs))
                chosen = [r for r in scanned if r["qualifies"]][:needed]
                save("selection_"+rival+".json", {"scanned": scanned, "selected": chosen})
                print("prefix", rival, len(scanned), "selected", len(chosen), "/", needed, flush=True)
            if len(chosen) < needed:
                save("coverage_failure.json", {"rival": rival, "passed": False})
                raise SystemExit("Insufficient branch coverage; no pass")
            panels[rival] = chosen
    save("panels.json", panels)
    rows = []
    report = {**fixed, "rows": rows, "complete": False, "passed": False}
    jobs = [(rival, role, r["seed"], seat) for rival, panel in panels.items() for r in panel for role in ("old", "new") for seat in (0, 1)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(play, j) for j in jobs]):
            row = f.result(); rows.append(row)
            save("confirmation.json", report)
            print(len(rows), "/128", row["rival"], row["role"], row["seed"], row["seat"], row["game"]["margin"], flush=True)
    scores = {rival: {role: sum(point(r["game"]) for r in rows if r["rival"] == rival and r["role"] == role)
                      for role in ("old", "new")} for rival in RIVALS}
    active = {rival: sum((r["game"].get("candidate_telemetry") or {}).get("farmice_turns", 0) > 0 for r in rows if r["rival"] == rival and r["role"] == "new") for rival in RIVALS}
    errors = sum((r["game"].get("candidate_telemetry") or {}).get(key, 0) for r in rows for key in ("queue_errors", "farmice_errors"))
    by = {(r["rival"], r["role"], r["seed"], r["seat"]): r["game"] for r in rows}
    parity = all(all(by["a2", "old", r["seed"], seat][key] == by["a2", "new", r["seed"], seat][key]
                     for key in ("candidate_reward", "opponent_reward")) for r in panels["a2"] for seat in (0, 1))
    checks = {"all_games": len(rows) == 128, "all_done": all(r["game"]["candidate_status"] == r["game"]["opponent_status"] == "DONE" for r in rows),
              "zero_errors": errors == 0, "external_activation": all(active[k] >= 20 for k in ("489", "C95")),
              "external_win_nonregression": all(scores[k]["new"] >= scores[k]["old"] for k in ("489", "C95")),
              "mirror_inactive": active["a2"] == 0, "mirror_cash_parity": parity}
    report.update(complete=True, passed=all(checks.values()), scores=scores, activation=active, checks=checks, errors=errors)
    save("confirmation.json", report)
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}), flush=True)
