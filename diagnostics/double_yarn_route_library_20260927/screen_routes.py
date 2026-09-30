"""Seat-0 fixed-route development screen of every complete prefix-compatible tape."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import main as source  # noqa: E402
from paired_benchmark import run_game  # noqa: E402

MAIN = ROOT / "main.py"
MAIN_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
PAIR = ("YARN_STORE", "YARN_STORE")
MANIFEST = json.loads((ROOT / "diagnostics" / "top10_goal_20260926" /
                       "double_yarn_highsheep_4routes_summary.json").read_text(encoding="utf8"))
ROUTES = tuple(sorted(route for route, tape in source._IMPL.chassis.routes.items()
                      if tape[:144] == source._IMPL.chassis.routes[9][:144]))


def play(job: tuple[int, int]) -> dict:
    route, case = job
    item = MANIFEST[case]
    mapping = dict(source._V92_TABLE)
    mapping[PAIR] = route
    result = run_game(str(MAIN), f"rawroute:{item['path']}", int(item["seed"]),
                      0, False, 144, {"_V92_TABLE": mapping})
    assert result["candidate_status"] == result["opponent_status"] == "DONE"
    assert tuple(result["candidate_capture"]["shops"][:2]) == PAIR
    return {"route": route, "case": case, "team": item["team"],
            "seed": item["seed"], "action_sha256": item["action_sha256"],
            "own": result["candidate_reward"],
            "rival": result["opponent_reward"],
            "margin": result["margin"],
            "max_call_ms": result["candidate_timing"]["max_ms"]}


def main() -> None:
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == MAIN_HASH
    assert len(MANIFEST) == 4
    assert len(ROUTES) == 40 and 9 in ROUTES
    jobs = [(route, case) for route in ROUTES for case in range(4)]
    results = []
    with ProcessPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(play, job): job for job in jobs}
        for future in as_completed(futures):
            results.append(future.result())
            if len(results) % 10 == 0:
                (HERE / "screen_partial.json").write_text(
                    json.dumps({"completed": len(results), "rows": results}, indent=2), encoding="utf8")
                print(f"completed {len(results)}/{len(jobs)}", flush=True)
    by = {(row["route"], row["case"]): row for row in results}
    baseline = [by[(9, case)] for case in range(4)]
    panel = json.loads((ROOT / "diagnostics" / "top100_refresh_2026-09-26_0708" /
                        "main_100routes.json").read_text(encoding="utf8"))
    existing = {row["action_sha256"]: next(game for game in row["games"]
                                             if game["candidate_seat"] == 0)
                for row in panel["rows"]}
    for row in baseline:
        previous = existing[row["action_sha256"]]
        assert (row["own"], row["rival"]) == (previous["candidate_reward"],
                                              previous["opponent_reward"])
    summaries = []
    for route in ROUTES:
        gains = [{"team": MANIFEST[case]["team"],
                  "delta_own": by[(route, case)]["own"] - baseline[case]["own"],
                  "delta_rival": by[(route, case)]["rival"] - baseline[case]["rival"],
                  "delta_margin": by[(route, case)]["margin"] - baseline[case]["margin"],
                  "margin": by[(route, case)]["margin"]}
                 for case in range(4)]
        targets = [row for row in gains if row["team"] != "dodsters"]
        control = next(row for row in gains if row["team"] == "dodsters")
        eligible = (all(row["delta_own"] > 0 and row["delta_margin"] > 0 for row in targets)
                    and max(row["delta_margin"] for row in targets) >= 5000
                    and control["delta_own"] >= -1000
                    and control["delta_margin"] >= -1000)
        summaries.append({"route": route, "eligible": eligible,
                          "min_target_margin_gain": min(row["delta_margin"] for row in targets),
                          "total_target_margin_gain": sum(row["delta_margin"] for row in targets),
                          "total_target_own_gain": sum(row["delta_own"] for row in targets),
                          "gains": gains})
    ranked = sorted((row for row in summaries if row["eligible"]),
                    key=lambda row: (-row["min_target_margin_gain"],
                                     -row["total_target_margin_gain"],
                                     -row["total_target_own_gain"], row["route"]))
    result = {"main_sha256": MAIN_HASH, "manifest": [
                  {key: item[key] for key in ("team", "seed", "source_seat", "action_sha256", "path")}
                  for item in MANIFEST],
              "route_ids": ROUTES, "baseline": baseline,
              "selected_route": ranked[0]["route"] if ranked else None,
              "eligible_routes": [row["route"] for row in ranked],
              "summaries": summaries, "rows": sorted(results, key=lambda row: (row["route"], row["case"]))}
    (HERE / "fixed_screen.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print("eligible", result["eligible_routes"], flush=True)
    print("top_min_gain", sorted(summaries, key=lambda row: -row["min_target_margin_gain"])[:5], flush=True)


if __name__ == "__main__":
    main()
