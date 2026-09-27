"""Screen all existing route IDs on three saved YARN_STORE,PIZZA_SHOP losses."""

from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

CANDIDATE = ROOT / "exp_route_probe_20260926.py"
LOSSES = ROOT / "diagnostics/top100_refresh_2026-09-26/losses_31_summary.json"
TEAMS = ("mtmr_s1", "YumeNeko", "Lucas Boesen")
SHOPS = ["YARN_STORE", "PIZZA_SHOP"]
OUTPUT = Path(__file__).with_name("route_id_search_yarn_pizza.json")


def play(job):
    route_id, team, entry = job
    row = run_game(str(CANDIDATE), f"rawroute:{entry['path']}", int(entry["seed"]),
                   0, False, None, {"_ROUTE_PROBE_ID": route_id,
                                    "_ROUTE_PROBE_SHOPS": SHOPS})
    return {
        "route_id": route_id, "team": team,
        "margin": row["margin"],
        "own_cash": row["candidate_reward"],
        "rival_cash": row["opponent_reward"],
        "status": [row["candidate_status"], row["opponent_status"]],
    }


def main():
    spec = importlib.util.spec_from_file_location("route_probe_listing_yarn", CANDIDATE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    ids = sorted(module._IMPL.chassis.routes)
    entries = json.loads(LOSSES.read_text(encoding="utf8"))
    by_team = {entry["team"]: entry for entry in entries}
    assert all(team in by_team for team in TEAMS)
    jobs = [(route_id, team, by_team[team]) for route_id in ids for team in TEAMS]
    rows = []
    with ProcessPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(play, job): job for job in jobs}
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(row["route_id"], row["team"], f"{row['margin']:+.0f}", flush=True)
    assert len(rows) == len(jobs)
    assert all(row["status"] == ["DONE", "DONE"] for row in rows)
    rankings = []
    for route_id in ids:
        part = [row for row in rows if row["route_id"] == route_id]
        rankings.append({
            "route_id": route_id,
            "wins": sum(row["margin"] > 0 for row in part),
            "margin_sum": sum(row["margin"] for row in part),
            "margins": {row["team"]: row["margin"] for row in part},
        })
    rankings.sort(key=lambda row: (-row["wins"], -row["margin_sum"]))
    OUTPUT.write_text(json.dumps({
        "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        "shops": SHOPS, "teams": TEAMS, "seat": 0,
        "route_ids": ids, "rankings": rankings, "rows": rows,
    }, indent=2), encoding="utf8")
    print("best", rankings[:8], flush=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
