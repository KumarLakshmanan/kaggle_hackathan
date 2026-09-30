"""Complete the frozen top-20 replay development gate after the pilot."""

from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game


def play(job):
    candidate, sha, row, seat = job
    assert hashlib.sha256(Path(candidate).read_bytes()).hexdigest() == sha
    game = run_game(candidate, "rawroute:" + row["path"], row["seed"], seat, False, 144, {})
    return {"team": row["team"], "team_id": row["team_id"], "rank": row["rank"],
            "episode_id": row["episode_id"], **game}


def main():
    build = json.loads((HERE / "build_manifest.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest() == build["plan_sha256"]
    assert hashlib.sha256(Path(build["candidate"]).read_bytes()).hexdigest() == build["candidate_sha256"]
    routes_path = ROOT / "diagnostics/current_top20_20260927_163500/routes/summary.json"
    routes = json.loads(routes_path.read_text(encoding="utf-8"))
    assert len(routes) == 20
    baseline_path = ROOT / "diagnostics/current_top20_20260927_163500/assessment.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert baseline["candidate_sha256"] == build["base_sha256"]
    old = {(g["team_id"], g["candidate_seat"]): g for g in baseline["games"]}
    pilot = json.loads((HERE / "pilot.json").read_text(encoding="utf-8"))
    assert pilot["complete"] and pilot["candidate_sha256"] == build["candidate_sha256"]
    used = {(g["team_id"], g["candidate_seat"]) for g in pilot["games"]}
    assert len(used) == 4
    jobs = [(build["candidate"], build["candidate_sha256"], row, seat)
            for row in routes for seat in (0, 1) if (row["team_id"], seat) not in used]
    assert len(jobs) == 36
    output = {"started_at_utc": datetime.now(timezone.utc).isoformat(),
              "candidate_sha256": build["candidate_sha256"],
              "plan_sha256": build["plan_sha256"],
              "routes_sha256": hashlib.sha256(routes_path.read_bytes()).hexdigest(),
              "baseline_sha256": hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
              "pilot_games_reused": 4, "games": list(pilot["games"]), "complete": False}
    def save():
        (HERE / "top20.json").write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    save()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(play, j) for j in jobs]):
            game = future.result()
            game["old_margin"] = old[game["team_id"], game["candidate_seat"]]["margin"]
            output["games"].append(game)
            save()
            print(len(output["games"]), game["team"], game["candidate_seat"],
                  game["old_margin"], game["margin"],
                  (game.get("candidate_telemetry") or {}).get("seed_prefund_turns"), flush=True)
    assert len(output["games"]) == 40
    paired = {}
    for game in output["games"]:
        paired.setdefault(game["team_id"], []).append(game)
    output["old_sweeps"] = sum(all(old[tid,seat]["margin"] > 0 for seat in (0, 1)) for tid in paired)
    output["new_sweeps"] = sum(len(pair) == 2 and all(g["margin"] > 0 for g in pair) for pair in paired.values())
    output["rescued_targets"] = [pair[0]["team"] for pair in paired.values()
                                  if pair[0]["team"] in ("Boey", "Vadim Vasilenko")
                                  and all(g["margin"] > 0 for g in pair)]
    output["lost_winning_seats"] = [{"team": g["team"], "seat": g["candidate_seat"],
                                      "old_margin": g["old_margin"], "new_margin": g["margin"]}
                                     for g in output["games"] if g["old_margin"] > 0 and g["margin"] <= 0]
    output["all_done"] = all(g["candidate_status"] == g["opponent_status"] == "DONE"
                             and g["frames"] == 720 for g in output["games"])
    output["error_rows"] = [{"team": g["team"], "seat": g["candidate_seat"], "key": key, "count": count}
                            for g in output["games"] for key, count in (g.get("candidate_telemetry") or {}).items()
                            if ("error" in key.lower() or "collision" in key.lower()) and count]
    output["activation_games"] = sum((g.get("candidate_telemetry") or {}).get("seed_prefund_turns", 0) > 0
                                     for g in output["games"])
    output["passed"] = bool(output["rescued_targets"] and not output["lost_winning_seats"]
                            and output["all_done"] and not output["error_rows"])
    output["complete"] = True
    output["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    save()
    print("RESULT", json.dumps({k: output[k] for k in ("old_sweeps", "new_sweeps", "rescued_targets",
                                                  "lost_winning_seats", "all_done", "error_rows",
                                                  "activation_games", "passed")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
